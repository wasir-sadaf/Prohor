
import { supabase, createUserClient } from "../config/supabase.js";

// Register
export const register = async (req, res) => {
    try {
        const { email, password, full_name } = req.body;

        if (!email || !password || !full_name) {
            return res.status(400).json({
                success: false,
                message: "All fields are required"
            });
        }

        // Create Supabase Auth account
        const { data, error } = await supabase.auth.signUp({
            email,
            password
        });

        if (error) {
            return res.status(400).json({
                success: false,
                message: error.message
            });
        }

        // Create user profile only when a session exists
        if (data.session && data.user) {
            const userClient = createUserClient(
                data.session.access_token
            );

            const { error: profileError } = await userClient
                .from("users")
                .upsert({
                    id: data.user.id,
                    full_name
                });

            if (profileError) {
                console.error("Profile creation error:", profileError);

                return res.status(500).json({
                    success: false,
                    message: "Account created, but profile creation failed"
                });
            }
        }

        return res.status(201).json({
            success: true,
            message: data.session
                ? "Registration successful"
                : "Registration successful. Please verify your email.",
            user: data.user,
            session: data.session
        });

    } catch (error) {
        console.error("Registration error:", error);

        return res.status(500).json({
            success: false,
            message: error.message
        });
    }
};


// Login
export const login = async (req, res) => {
    try {
        const { email, password } = req.body;

        if (!email || !password) {
            return res.status(400).json({
                success: false,
                message: "Email and password are required"
            });
        }

        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password
        });

        if (error) {
            return res.status(401).json({
                success: false,
                message: error.message
            });
        }

        return res.status(200).json({
            success: true,
            message: "Login successful",
            user: data.user,
            session: data.session
        });

    } catch (error) {
        console.error("Login error:", error);

        return res.status(500).json({
            success: false,
            message: error.message
        });
    }
};


// Get current user
export const getMe = async (req, res) => {
    try {
        const { data, error } = await req.supabase
            .from("users")
            .select("*")
            .eq("id", req.user.id)
            .single();

        if (error) {
            return res.status(404).json({
                success: false,
                message: "User profile not found"
            });
        }

        return res.status(200).json({
            success: true,
            user: data
        });

    } catch (error) {
        console.error("Get profile error:", error);

        return res.status(500).json({
            success: false,
            message: error.message
        });
    }
};
