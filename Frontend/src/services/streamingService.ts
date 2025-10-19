/**
 * Streaming service for real-time agent progress updates
 * Uses Server-Sent Events (SSE) to stream agent thinking process
 */

export interface StreamEventData {
  response?: string;
  symbols_analyzed?: string[];
  stock_data?: Record<string, unknown>;
  statement_data?: Record<string, unknown>;
  analysis_results?: Record<string, unknown>;
  symbols?: string[];
}

export interface StreamEvent {
  type: 'status' | 'step' | 'iteration' | 'tool_start' | 'tool_success' | 'tool_error' | 'tool_skip' | 'complete' | 'error' | 'warning';
  step?: string;
  message: string;
  reasoning?: string;  // Added: Detailed reasoning/insight for why agent is doing this action
  progress?: number;
  tool?: string;
  symbol?: string;
  iteration?: number;
  data?: StreamEventData;
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const streamAgentQuery = async (
  query: string,
  sessionId: string,
  userId: string,
  onProgress: (event: StreamEvent) => void,
  onComplete: (data: StreamEventData) => void,
  onError: (error: string) => void
): Promise<void> => {
  try {
    console.log('📤 Sending query:', { query, sessionId, userId });
    
    const response = await fetch(`${API_BASE_URL}/agent/query-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        query,
        session_id: sessionId,
        user_id: userId
      }),
    });

    console.log('📥 Response status:', response.status, response.statusText);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Response error:', errorText);
      throw new Error(`Stream failed (${response.status}): ${errorText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No reader available');
    }

    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }

      // Decode the chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });

      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          
          if (data === '[DONE]') {
            return;
          }

          try {
            const event: StreamEvent = JSON.parse(data);
            
            console.log('📨 Event received:', event.type, event.message);
            
            // Send progress update
            onProgress(event);

            // Handle completion
            if (event.type === 'complete' && event.data) {
              console.log('✅ Query complete:', event.data);
              onComplete(event.data);
            }

            // Handle errors
            if (event.type === 'error') {
              console.error('❌ Agent error:', event.message);
              onError(event.message);
            }
          } catch (e) {
            console.error('Failed to parse SSE event:', e, 'Data:', data);
          }
        }
      }
    }
  } catch (error) {
    console.error('Stream error:', error);
    onError(error instanceof Error ? error.message : 'Unknown streaming error');
  }
};
