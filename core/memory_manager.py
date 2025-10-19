"""
Hybrid Memory Manager for Agent Conversations
Combines in-memory cache with database persistence for optimal performance.

Two-Tier Architecture:
- Tier 1: In-memory lightweight metadata (fast, for immediate follow-ups)
- Tier 2: Database cumulative context (persistent, for long conversations & old chats)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from supabase import Client
from config.settings import get_settings
from core.utils import logger
import uuid


class HybridMemoryManager:
    """
    Two-tier memory system for conversation management.
    
    Features:
    - In-memory cache for active sessions (30-min TTL)
    - Database storage for persistence
    - Cumulative context generation every 3 messages
    - Lightweight metadata for immediate follow-ups
    """
    
    def __init__(self, supabase_client: Client):
        """Initialize hybrid memory manager."""
        self.supabase = supabase_client
        self.settings = get_settings()
        
        # Tier 1: In-memory cache for active sessions
        self.active_sessions = {}  # {session_id: session_data}
        self.cache_ttl_minutes = 30
        
        logger.info("HybridMemoryManager: Initialized with two-tier memory system")
    
    # ==================== SESSION MANAGEMENT ====================
    
    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Get existing session or create new one.
        Checks memory cache first, then database.
        
        Returns:
            {
                'conversation_id': UUID,
                'session_id': str,
                'is_new': bool,
                'context': str,
                'message_count': int
            }
        """
        # Generate session_id if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"HybridMemory: Generated new session_id: {session_id}")
        
        # Check Tier 1: In-memory cache
        if session_id in self.active_sessions:
            cache_entry = self.active_sessions[session_id]
            
            if self._is_cache_valid(cache_entry['last_access']):
                logger.info(f"HybridMemory: Cache HIT for {session_id}")
                cache_entry['last_access'] = datetime.now()
                return {
                    'session_id': session_id,
                    'is_new': False,
                    'context': cache_entry['context'],
                    'message_count': cache_entry['message_count']
                }
            else:
                logger.info(f"HybridMemory: Cache EXPIRED for {session_id}")
                del self.active_sessions[session_id]
        
        # Check Tier 2: Database
        logger.info(f"HybridMemory: Cache MISS, checking database")
        conversation = self._get_conversation_from_db(session_id)
        
        if conversation:
            # Existing conversation - restore
            logger.info(f"HybridMemory: Restoring conversation {session_id}")
            context = self._build_context_for_session(session_id)
            
            # Cache in memory
            self.active_sessions[session_id] = {
                'session_id': session_id,
                'context': context,
                'message_count': 0,  # Will be counted from messages
                'last_access': datetime.now()
            }
            
            return {
                'session_id': session_id,
                'is_new': False,
                'context': context,
                'message_count': 0
            }
        else:
            # New conversation
            logger.info(f"HybridMemory: Creating new conversation")
            conversation = self._create_conversation_in_db(user_id, session_id)
            
            self.active_sessions[session_id] = {
                'session_id': session_id,
                'context': "",
                'message_count': 0,
                'last_access': datetime.now()
            }
            
            return {
                'session_id': session_id,
                'is_new': True,
                'context': "",
                'message_count': 0
            }
    
    def _is_cache_valid(self, last_access: datetime) -> bool:
        """Check if cache entry is still valid."""
        age_minutes = (datetime.now() - last_access).total_seconds() / 60
        return age_minutes < self.cache_ttl_minutes
    
    # ==================== CONTEXT BUILDING ====================
    
    def build_short_term_context(self, session_id: str) -> str:
        """
        Build context for follow-up questions using lightweight metadata.
        This is the PUBLIC method called by agents.
        """
        return self._build_context_for_session(session_id)
    
    def _build_context_for_session(
        self,
        session_id: str
    ) -> str:
        """
        Build context string from conversation history.
        Uses cumulative context + recent metadata.
        """
        try:
            # Get last cumulative context (if exists)
            cumulative = self._get_last_cumulative_context(session_id)
            
            # Get recent messages metadata
            recent_metadata = self._get_recent_metadata(session_id, limit=2)
            
            if not cumulative and not recent_metadata:
                return ""
            
            # Build context string
            parts = []
            
            if cumulative:
                parts.append(f"Conversation summary:\n{cumulative}")
            
            if recent_metadata:
                parts.append("\nRecent activity:")
                for meta in recent_metadata:
                    parts.append(f"- {meta}")
            
            return "\n".join(parts)
        
        except Exception as e:
            logger.error(f"Error building context: {e}")
            return ""
    
    def _get_last_cumulative_context(self, session_id: str) -> Optional[str]:
        """Get the most recent cumulative context."""
        try:
            result = self.supabase.table('messages') \
                .select('cumulative_context') \
                .eq('session_id', session_id) \
                .not_.is_('cumulative_context', 'null') \
                .order('created_at', desc=True) \
                .limit(1) \
                .execute()
            
            if result.data and result.data[0].get('cumulative_context'):
                return result.data[0]['cumulative_context']
            return None
        
        except Exception as e:
            logger.warning(f"Could not fetch cumulative context: {e}")
            return None
    
    def _get_recent_metadata(
        self,
        session_id: str,
        limit: int = 2
    ) -> List[str]:
        """Get recent message metadata summaries."""
        try:
            result = self.supabase.table('messages') \
                .select('role, metadata') \
                .eq('session_id', session_id) \
                .eq('role', 'user') \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            if not result.data:
                return []
            
            summaries = []
            for msg in reversed(result.data):  # Reverse to chronological order
                metadata = msg.get('metadata', {})
                # Build summary from metadata
                symbols = metadata.get('symbols', [])
                query_type = metadata.get('query_type', 'general')
                if symbols:
                    summaries.append(f"User analyzed {', '.join(symbols)} ({query_type})")
            
            return summaries
        
        except Exception as e:
            logger.warning(f"Could not fetch metadata: {e}")
            return []
    
    # ==================== MESSAGE STORAGE ====================
    
    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> int:
        """
        Save message to database and update cache.
        Returns message count for this conversation.
        """
        try:
            # Prepare message data
            message_data = {
                'session_id': session_id,
                'role': role,
                'content': content,
                'metadata': metadata or {}
            }
            
            # Save to database
            self.supabase.table('messages').insert(message_data).execute()
            
            # Update conversation timestamp
            self.supabase.table('conversations') \
                .update({'updated_at': datetime.now().isoformat()}) \
                .eq('session_id', session_id) \
                .execute()
            
            # Get updated message count
            message_count = self._get_message_count(session_id)
            
            # Update in-memory cache
            if session_id in self.active_sessions:
                cache_entry = self.active_sessions[session_id]
                cache_entry['message_count'] = message_count
                cache_entry['last_access'] = datetime.now()
            
            logger.info(f"HybridMemory: Saved {role} message (count: {message_count})")
            return message_count
        
        except Exception as e:
            logger.error(f"HybridMemory: Error saving message: {e}")
            return 0
    
    def _get_message_count(self, session_id: str) -> int:
        """Get total message count for conversation."""
        try:
            result = self.supabase.table('messages') \
                .select('id', count='exact') \
                .eq('session_id', session_id) \
                .execute()
            
            return result.count if hasattr(result, 'count') else 0
        except Exception as e:
            logger.warning(f"Could not get message count: {e}")
            return 0
    
    # ==================== CUMULATIVE CONTEXT GENERATION ====================
    
    def should_generate_cumulative_context(self, message_count: int) -> bool:
        """Check if we should generate cumulative context (every 3 messages)."""
        return message_count > 0 and message_count % 3 == 0
    
    def generate_cumulative_context(
        self,
        session_id: str,
        llm_instance
    ) -> Optional[str]:
        """
        Generate cumulative context summary of entire conversation.
        Called every 3 messages.
        
        Returns generated context string.
        """
        try:
            logger.info(f"HybridMemory: Generating cumulative context for {session_id}")
            
            # Get previous cumulative context (if exists)
            previous_context = self._get_last_cumulative_context(session_id)
            
            # Get all messages since last context generation
            messages = self._get_messages_since_last_context(session_id)
            
            if not messages:
                return None
            
            # Build prompt for context generation
            if previous_context:
                # Update existing context
                prompt = self._build_update_context_prompt(previous_context, messages)
            else:
                # First-time context generation
                prompt = self._build_initial_context_prompt(messages)
            
            # Call LLM
            from langchain_core.messages import HumanMessage, SystemMessage
            
            response = llm_instance.invoke([
                SystemMessage(content="You are a conversation summarizer. Be concise but capture key insights."),
                HumanMessage(content=prompt)
            ])
            
            cumulative_context = response.content.strip()
            
            logger.info(f"HybridMemory: Generated context ({len(cumulative_context)} chars)")
            return cumulative_context
        
        except Exception as e:
            logger.error(f"HybridMemory: Error generating context: {e}")
            return None
    
    def save_cumulative_context(
        self,
        session_id: str,
        cumulative_context: str
    ):
        """Save cumulative context to the most recent message."""
        try:
            # Get most recent message
            result = self.supabase.table('messages') \
                .select('id') \
                .eq('session_id', session_id) \
                .order('created_at', desc=True) \
                .limit(1) \
                .execute()
            
            if result.data:
                message_id = result.data[0]['id']
                
                # Update with cumulative context
                self.supabase.table('messages') \
                    .update({'cumulative_context': cumulative_context}) \
                    .eq('id', message_id) \
                    .execute()
                
                logger.info(f"HybridMemory: Saved cumulative context to message {message_id}")
        
        except Exception as e:
            logger.error(f"HybridMemory: Error saving cumulative context: {e}")
    
    def _get_messages_since_last_context(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get messages since last cumulative context was generated."""
        try:
            # Get ID of last message with cumulative context
            last_context_result = self.supabase.table('messages') \
                .select('id, created_at') \
                .eq('session_id', session_id) \
                .not_.is_('cumulative_context', 'null') \
                .order('created_at', desc=True) \
                .limit(1) \
                .execute()
            
            query = self.supabase.table('messages') \
                .select('role, content, metadata') \
                .eq('session_id', session_id) \
                .order('created_at', desc=False) \
                .limit(limit)
            
            if last_context_result.data:
                # Get messages after last context
                last_timestamp = last_context_result.data[0]['created_at']
                query = query.gt('created_at', last_timestamp)
            
            result = query.execute()
            return result.data if result.data else []
        
        except Exception as e:
            logger.warning(f"Error fetching messages: {e}")
            return []
    
    def _build_initial_context_prompt(self, messages: List[Dict]) -> str:
        """Build prompt for first-time context generation."""
        message_text = "\n".join([
            f"- {msg['role']}: {msg['content'][:100]}"
            for msg in messages
        ])
        
        return f"""Summarize this financial analysis conversation in 2-3 sentences.

Messages:
{message_text}

Focus on:
1. What stocks/companies are being analyzed
2. Key findings or insights discovered
3. User's current focus or decision point

Provide a concise summary:"""
    
    def _build_update_context_prompt(
        self,
        previous_context: str,
        new_messages: List[Dict]
    ) -> str:
        """Build prompt for updating existing context."""
        message_text = "\n".join([
            f"- {msg['role']}: {msg['content'][:100]}"
            for msg in new_messages
        ])
        
        return f"""Update the conversation summary with new developments.

Previous summary:
{previous_context}

New messages:
{message_text}

Generate an UPDATED 2-3 sentence summary of the ENTIRE conversation.
- Include important points from the previous summary
- Add new developments from recent messages
- Remove outdated details if needed

Updated summary:"""
    
    # ==================== DATABASE OPERATIONS ====================
    
    def _get_conversation_from_db(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation from database."""
        try:
            result = self.supabase.table('conversations') \
                .select('*') \
                .eq('session_id', session_id) \
                .single() \
                .execute()
            return result.data if result.data else None
        except Exception:
            return None
    
    def _create_conversation_in_db(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Create new conversation in database."""
        result = self.supabase.table('conversations').insert({
            'user_id': user_id,
            'session_id': session_id,
            'title': 'New Conversation'
        }).execute()
        
        return result.data[0] if result.data else None
    
    def _update_conversation_title_if_new(
        self,
        conversation_id: str,
        first_query: str
    ):
        """Update conversation title if still 'New Conversation'."""
        try:
            result = self.supabase.table('conversations') \
                .select('title') \
                .eq('id', conversation_id) \
                .single() \
                .execute()
            
            if result.data and result.data.get('title') == 'New Conversation':
                title = first_query[:57] + "..." if len(first_query) > 60 else first_query
                
                self.supabase.table('conversations') \
                    .update({'title': title}) \
                    .eq('id', conversation_id) \
                    .execute()
        except Exception as e:
            logger.warning(f"Could not update title: {e}")
    
    # ==================== CONVERSATION LIST ====================
    
    def list_user_conversations(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get list of user's conversations for UI."""
        try:
            result = self.supabase.table('conversations') \
                .select('session_id, title, updated_at') \
                .eq('user_id', user_id) \
                .order('updated_at', desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []
