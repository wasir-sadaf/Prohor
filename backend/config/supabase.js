import dotenv from "dotenv";
dotenv.config();

import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY;

// Public client for authentication
export const supabase = createClient(
    supabaseUrl,
    supabaseAnonKey
);

// User-specific client for database operations.
// This forwards the user's JWT so Supabase RLS policies apply.
export const createUserClient = (token) => {
    return createClient(
        supabaseUrl,
        supabaseAnonKey,
        {
            global: {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        }
    );
};