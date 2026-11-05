import express from "express";

import {
    searchLegal,
    getLegalSource
} from "../controllers/legalController.js";

import authMiddleware from "../middleware/authMiddleware.js";

const router = express.Router();

router.use(authMiddleware);

router.get("/search", searchLegal);
router.get("/sources/:id", getLegalSource);

export default router;