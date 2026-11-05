// Search legal information
export const searchLegal = async (req, res) => {
    try {
        const { q } = req.query;

        if (!q || !q.trim()) {
            return res.status(400).json({
                success: false,
                message: "Search query is required"
            });
        }

        const { data, error } = await req.supabase
            .from("legal_chunks")
            .select("*")
            .ilike("content", `%${q}%`)
            .limit(20);

        if (error) throw error;

        return res.status(200).json({
            success: true,
            results: data
        });

    } catch (error) {
        return res.status(500).json({
            success: false,
            message: error.message
        });
    }
};


// Get legal source details
export const getLegalSource = async (req, res) => {
    try {
        const { id } = req.params;

        const { data, error } = await req.supabase
            .from("legal_sources")
            .select("*")
            .eq("id", id)
            .single();

        if (error) {
            return res.status(404).json({
                success: false,
                message: "Legal source not found"
            });
        }

        return res.status(200).json({
            success: true,
            source: data
        });

    } catch (error) {
        return res.status(500).json({
            success: false,
            message: error.message
        });
    }
};