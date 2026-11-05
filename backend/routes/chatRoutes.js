import express from "express";

import {
    sendMessage,
    getConversations,
    getMessages
} from "../controllers/chatController.js";

import authMiddleware from "../middleware/authMiddleware.js";

const router = express.Router();

router.use(authMiddleware);

router.post("/", sendMessage);
router.get("/conversations", getConversations);
router.get("/conversations/:conversationId/messages", getMessages);

export default router;