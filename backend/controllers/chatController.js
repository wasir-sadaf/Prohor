
export const sendMessage = async (req, res) => {
    try {
        const { message, conversation_id } = req.body;

        if (typeof message !== "string" || !message.trim()) {
            return res.status(400).json({
                success: false,
                message: "Message is required"
            });
        }

        const db = req.supabase;
        const userId = req.user.id;

        let conversationId = conversation_id;

        // Create a new conversation if needed
        if (!conversationId) {
            const { data, error } = await db
                .from("conversations")
                .insert({
                    user_id: userId,
                    title: message.trim().substring(0, 60)
                })
                .select()
                .single();

            if (error) throw error;

            conversationId = data.id;

        } else {
            // Verify conversation ownership
            const { data, error } = await db
                .from("conversations")
                .select("id")
                .eq("id", conversationId)
                .eq("user_id", userId)
                .single();

            if (error || !data) {
                return res.status(404).json({
                    success: false,
                    message: "Conversation not found"
                });
            }
        }

        // Save user message
        const { data: savedMessage, error: messageError } = await db
            .from("messages")
            .insert({
                conversation_id: conversationId,
                role: "user",
                content: message.trim()
            })
            .select()
            .single();

        if (messageError) throw messageError;

        // Update conversation timestamp
        const { error: updateError } = await db
            .from("conversations")
            .update({
                updated_at: new Date().toISOString()
            })
            .eq("id", conversationId)
            .eq("user_id", userId);

        if (updateError) throw updateError;

        return res.status(201).json({
            success: true,
            message: "Message saved successfully",
            conversation_id: conversationId,
            data: savedMessage
        });

    } catch (error) {
        console.error("Chat error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to save message"
        });
    }
};


// Get conversation history
export const getConversations = async (req, res) => {
    try {
        const { data, error } = await req.supabase
            .from("conversations")
            .select("*")
            .eq("user_id", req.user.id)
            .order("updated_at", { ascending: false });

        if (error) throw error;

        return res.status(200).json({
            success: true,
            conversations: data
        });

    } catch (error) {
        console.error("Get conversations error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to retrieve conversations"
        });
    }
};


// Get messages from a conversation
export const getMessages = async (req, res) => {
    try {
        const { conversationId } = req.params;
        const userId = req.user.id;

        // Verify conversation ownership first
        const { data: conversation, error: conversationError } =
            await req.supabase
                .from("conversations")
                .select("id")
                .eq("id", conversationId)
                .eq("user_id", userId)
                .single();

        if (conversationError || !conversation) {
            return res.status(404).json({
                success: false,
                message: "Conversation not found"
            });
        }

        // Retrieve messages
        const { data, error } = await req.supabase
            .from("messages")
            .select("*")
            .eq("conversation_id", conversationId)
            .order("created_at", { ascending: true });

        if (error) throw error;

        return res.status(200).json({
            success: true,
            messages: data
        });

    } catch (error) {
        console.error("Get messages error:", error);

        return res.status(500).json({
            success: false,
            message: "Failed to retrieve messages"
        });
    }
};
