# Supabase Integration Setup Guide

This guide walks you through setting up Supabase for caching Alpha Vantage API data in your Financial Agent application.

## Prerequisites

- Supabase account (free tier available)
- Python environment with the financial agent project

## Step 1: Create Supabase Project

1. **Sign up for Supabase**

   - Go to [https://supabase.com](https://supabase.com)
   - Sign up with your email or GitHub account
   - Create a new project

2. **Note down credentials**
   - After creating the project, go to **Settings** > **API**
   - Copy the **Project URL** (e.g., `https://your-project.supabase.co`)
   - Copy the **anon public key** (starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)

## Step 2: Create Database Table

1. **Open SQL Editor**

   - In your Supabase project dashboard, go to **SQL Editor**
   - Click **New query**

2. **Execute the following SQL**

   ```sql
   -- Create the stock_overview table
   CREATE TABLE IF NOT EXISTS stock_overview (
       id BIGSERIAL PRIMARY KEY,
       symbol TEXT NOT NULL UNIQUE,
       data JSONB NOT NULL,
       last_updated TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
       created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
   );

   -- Create indexes for better performance
   CREATE INDEX IF NOT EXISTS idx_stock_overview_symbol ON stock_overview (symbol);
   CREATE INDEX IF NOT EXISTS idx_stock_overview_last_updated ON stock_overview (last_updated);

   -- Enable Row Level Security (RLS)
   ALTER TABLE stock_overview ENABLE ROW LEVEL SECURITY;

   -- Create policy to allow public access (adjust as needed for production)
   CREATE POLICY "Allow public access" ON stock_overview
       FOR ALL USING (true);
   ```

3. **Run the query**
   - Click **Run** to execute the SQL
   - You should see "Success. No rows returned" message

## Step 3: Install Dependencies

1. **Install Supabase Python client**

   ```bash
   pip install supabase
   ```

   Or if you're using the requirements.txt (already updated):

   ```bash
   pip install -r requirements.txt
   ```

## Step 4: Configure Environment Variables

1. **Create or update your `.env` file**

   ```env
   # Alpha Vantage API (existing)
   ALPHAVANTAGE_API_KEY=your_alpha_vantage_key

   # Google AI (existing)
   GOOGLE_API_KEY=your_google_api_key

   # Supabase Configuration (new)
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key_here
   ```

2. **Environment variable names mapping**
   - In Supabase dashboard: `Project URL` → In .env: `SUPABASE_URL`
   - In Supabase dashboard: `anon public key` → In .env: `SUPABASE_ANON_KEY`

## Step 5: Test the Integration

1. **Create a test script** (`test_supabase.py`)

   ```python
   import asyncio
   import os
   from tools.alphavantage_api import AlphaVantageAPI
   from database.supabase_client import SupabaseManager

   async def test_supabase():
       # Test direct Supabase connection
       try:
           db = SupabaseManager()
           health = db.health_check()
           print("Supabase Health Check:", health)

           stats = db.get_cache_stats()
           print("Cache Stats:", stats)
       except Exception as e:
           print("Supabase connection error:", e)
           return

       # Test Alpha Vantage with caching
       api = AlphaVantageAPI()

       print("\\n--- First request (should fetch from API) ---")
       result1 = api.fetch_company_overview("AAPL")
       print("Cache hit:", result1.get('cache_info', {}).get('cache_hit', 'Unknown'))
       print("Data source:", result1.get('cache_info', {}).get('data_source', 'Unknown'))

       print("\\n--- Second request (should use cache) ---")
       result2 = api.fetch_company_overview("AAPL")
       print("Cache hit:", result2.get('cache_info', {}).get('cache_hit', 'Unknown'))
       print("Data source:", result2.get('cache_info', {}).get('data_source', 'Unknown'))

   if __name__ == "__main__":
       asyncio.run(test_supabase())
   ```

2. **Run the test**
   ```bash
   python test_supabase.py
   ```

## Step 6: Verify in Supabase Dashboard

1. **Check the data**

   - Go to **Table Editor** in Supabase
   - Select the `stock_overview` table
   - You should see cached stock data after running the test

2. **Monitor logs**
   - Check your application logs for messages like:
     - `SupabaseManager: Successfully initialized Supabase client`
     - `AlphaVantageAPI: Returning cached data from Supabase for AAPL`
     - `AlphaVantageAPI: Cache miss - fetching fresh data from Alpha Vantage API`

## Troubleshooting

### Common Issues

1. **Import Error: `supabase` module not found**

   ```bash
   pip install supabase
   ```

2. **Authentication Error**

   - Double-check your `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
   - Ensure there are no extra spaces or quotes in the values

3. **Table doesn't exist**

   - Re-run the SQL commands in Step 2
   - Check that RLS policies are correctly set

4. **Permission Denied**
   - Verify RLS policy allows access
   - In production, create more restrictive policies

### Environment Variable Debugging

Add this to test your environment variables:

```python
import os
print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_ANON_KEY:", os.getenv("SUPABASE_ANON_KEY")[:20] + "..." if os.getenv("SUPABASE_ANON_KEY") else None)
```

## Production Considerations

1. **Security**

   - Use service role key for server-side operations
   - Implement proper RLS policies
   - Consider API rate limiting

2. **Performance**

   - Monitor cache hit rates
   - Adjust TTL (currently 24 hours) based on needs
   - Consider adding database indexes for specific queries

3. **Monitoring**
   - Set up Supabase webhooks for monitoring
   - Log cache performance metrics
   - Monitor API usage and costs

## Cache Behavior

- **Cache TTL**: 24 hours (configurable)
- **Cache Key**: Stock symbol (uppercase)
- **Cache Miss**: Automatically fetches from Alpha Vantage and caches
- **Background Saving**: Cache saves happen asynchronously to avoid delays
- **Error Handling**: Falls back to direct API calls if cache fails

## Success Indicators

✅ Supabase client initializes successfully  
✅ First API call logs "Cache miss" and fetches from Alpha Vantage  
✅ Second API call logs "Cache hit" and returns from Supabase  
✅ Data appears in Supabase table editor  
✅ No import errors or connection issues

Your Supabase integration is now ready! The Financial Agent will automatically use cached data when available and fetch fresh data when needed.
