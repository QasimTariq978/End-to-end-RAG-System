-- Newer Supabase projects don't auto-grant table privileges to the API roles.
-- Signed-in users get table access here; RLS policies still limit them to their own rows.
-- anon gets nothing.
grant select, insert, update, delete on public.threads to authenticated;
grant select, insert, update, delete on public.messages to authenticated;
