import { supabase, createUserClient } from "../config/supabase.js";

const authMiddleware = async (req, res, next) => {
    try {
        const authHeader = req.headers.authorization;

        if (!authHeader || !authHeader.startsWith("Bearer ")) {
            return res.status(401).json({
                success: false,
                message: "Authentication token required"
            });
        }

        const token = authHeader.split(" ")[1];

        const { data, error } = await supabase.auth.getUser(token);

        if (error || !data.user) {
            return res.status(401).json({
                success: false,
                message: "Invalid or expired token"
            });
        }

        req.user = data.user;
        req.supabase = createUserClient(token);

        next();

    } catch (error) {
        return res.status(500).json({
            success: false,
            message: "Authentication failed"
        });
    }
};

export default authMiddleware;