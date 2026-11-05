// Get all legal documents
export const getDocuments = async (req, res) => {
    try {
        const { data, error } = await req.supabase
            .from("legal_sources")
            .select("*")
            .order("created_at", { ascending: false });

        if (error) throw error;

        return res.status(200).json({
            success: true,
            documents: data
        });

    } catch (error) {
        return res.status(500).json({
            success: false,
            message: error.message
        });
    }
};


// Get a specific legal document
export const getDocumentById = async (req, res) => {
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
                message: "Document not found"
            });
        }

        return res.status(200).json({
            success: true,
            document: data
        });

    } catch (error) {
        return res.status(500).json({
            success: false,
            message: error.message
        });
    }
};