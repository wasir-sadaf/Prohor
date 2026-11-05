import express from "express";

import {
    getDocuments,
    getDocumentById
} from "../controllers/documentController.js";

import authMiddleware from "../middleware/authMiddleware.js";

const router = express.Router();

router.use(authMiddleware);

router.get("/", getDocuments);
router.get("/:id", getDocumentById);

export default router;