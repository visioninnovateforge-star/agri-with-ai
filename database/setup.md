# Supabase Setup Instructions

This file contains instructions for setting up your Supabase database for the Agriculture Insights Platform.

## Prerequisites

1. Create a Supabase account at [supabase.com](https://supabase.com)
2. Create a new project in Supabase

## Database Setup

### Step 1: Create Tables

1. Go to your Supabase dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of `schema.sql` into the SQL editor
4. Execute the queries to create all tables, indexes, and policies

### Step 2: Configure Environment Variables

1. Go to Settings > API in your Supabase dashboard
2. Copy your Project URL and anon/public key
3. Create a `.env` file in the backend directory with:

```env
SUPABASE_URL=your_project_url_here
SUPABASE_KEY=your_anon_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
```

### Step 3: Authentication Setup

The application uses custom JWT authentication alongside Supabase's database features. The RLS policies are configured to work with custom user IDs.

### Step 4: Test Data

The schema includes sample test data:
- A sample farmer user
- A sample agronomist user  
- A sample researcher user
- Sample farmer profile data

### Step 5: Row Level Security (RLS)

RLS is enabled with the following access patterns:
- **Farmers**: Can only access their own data
- **Agronomists**: Can view all farmer data and validate predictions
- **Researchers**: Can access aggregated data and export datasets

## API Integration

The FastAPI backend connects to Supabase using the `supabase-py` client library. The connection is configured in `app/models/database.py`.

## Security Notes

1. Never commit your `.env` file to version control
2. Use strong JWT secret keys in production
3. RLS policies are enforced at the database level
4. All API endpoints include role-based access control

## Database Maintenance

- Use Supabase's built-in backup features
- Monitor query performance in the dashboard
- Set up monitoring and alerts for production usage

## Troubleshooting

- Check Supabase logs for database errors
- Verify RLS policies if access issues occur
- Ensure environment variables are correctly set
- Check API key permissions and expiration