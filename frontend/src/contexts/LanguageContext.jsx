import { createContext, useContext, useState } from "react";

const LanguageContext = createContext(null);

const translations = {
  bn: {
    // Nav
    home: "হোম",
    chat: "আইনি সহায়তা",
    documents: "আইনি দলিল",
    search: "অনুসন্ধান",
    login: "লগইন",
    register: "নিবন্ধন",
    logout: "লগআউট",
    profile: "প্রোফাইল",

    // Home
    heroTitle: "আইন বুঝুন, অধিকার জানুন",
    heroSubtitle: "প্রহর আপনাকে বাংলাদেশের আইন সহজ ভাষায় বুঝতে ও আপনার অধিকার জানতে সাহায্য করে।",
    getStarted: "শুরু করুন",
    learnMore: "আরও জানুন",

    // Features
    featuresTitle: "প্রহর আপনাকে কীভাবে সাহায্য করে?",
    feature1Title: "আইনি প্রশ্নের উত্তর",
    feature1Desc: "আপনার আইনি প্রশ্নের সহজ ও বোধগম্য উত্তর পান বাংলায়।",
    feature2Title: "অধিকার জানুন",
    feature2Desc: "নাগরিক হিসেবে আপনার আইনি অধিকার ও সুরক্ষা সম্পর্কে জানুন।",
    feature3Title: "দলিল ব্যাখ্যা",
    feature3Desc: "জটিল আইনি দলিল সহজ ভাষায় বুঝুন এবং গুরুত্বপূর্ণ ধারা চিহ্নিত করুন।",
    feature4Title: "অভিযোগ সহায়তা",
    feature4Desc: "অভিযোগ ও জিডি আবেদনের খসড়া তৈরিতে সাহায্য পান।",
    feature5Title: "আইনি সহায়তা খুঁজুন",
    feature5Desc: "প্রাসঙ্গিক আইনি সেবা ও কর্তৃপক্ষের সাথে যোগাযোগ করুন।",
    feature6Title: "পরিস্থিতি গাইড",
    feature6Desc: "বাস্তব আইনি পরিস্থিতিতে ধাপে ধাপে নির্দেশনা পান।",

    // Chat
    chatPlaceholder: "আপনার আইনি প্রশ্ন লিখুন...",
    send: "পাঠান",
    newChat: "নতুন কথোপকথন",
    conversations: "কথোপকথন",
    noConversations: "কোনো কথোপকথন নেই",
    thinking: "চিন্তা করছে...",

    // Auth
    email: "ইমেইল",
    password: "পাসওয়ার্ড",
    fullName: "পুরো নাম",
    loginTitle: "প্রহরে লগইন করুন",
    registerTitle: "প্রহরে নিবন্ধন করুন",
    noAccount: "অ্যাকাউন্ট নেই?",
    hasAccount: "অ্যাকাউন্ট আছে?",

    // Documents
    documentsTitle: "আইনি দলিলসমূহ",
    searchDocuments: "দলিল অনুসন্ধান করুন...",
    verified: "যাচাইকৃত",
    noDocuments: "কোনো দলিল পাওয়া যায়নি",

    // Search
    searchTitle: "আইনি তথ্য অনুসন্ধান",
    searchPlaceholder: "আইন, ধারা বা বিষয় লিখুন...",
    searchButton: "অনুসন্ধান",
    noResults: "কোনো ফলাফল পাওয়া যায়নি",

    // Disclaimer
    disclaimer: "প্রহর সাধারণ আইনি তথ্য প্রদান করে, পেশাদার আইনি পরামর্শ নয়।",

    // Footer
    tagline: "আইন বুঝুন, অধিকার জানুন।",
    copyright: "© ২০২৬ প্রহর। সর্বস্বত্ব সংরক্ষিত।",
  },
  en: {
    home: "Home",
    chat: "Legal Help",
    documents: "Legal Documents",
    search: "Search",
    login: "Login",
    register: "Register",
    logout: "Logout",
    profile: "Profile",

    heroTitle: "Understand the Law, Know Your Rights",
    heroSubtitle: "Prohor helps Bangladeshi citizens understand laws and know their legal rights through simple explanations.",
    getStarted: "Get Started",
    learnMore: "Learn More",

    featuresTitle: "How can Prohor help you?",
    feature1Title: "Legal Q&A",
    feature1Desc: "Get clear and understandable answers to your legal questions.",
    feature2Title: "Know Your Rights",
    feature2Desc: "Learn about your legal rights and protections as a citizen.",
    feature3Title: "Document Explainer",
    feature3Desc: "Understand complex legal documents with simplified explanations.",
    feature4Title: "Complaint Assistant",
    feature4Desc: "Get help drafting complaints and GD applications.",
    feature5Title: "Find Legal Help",
    feature5Desc: "Connect with relevant legal aid services and authorities.",
    feature6Title: "Scenario Guide",
    feature6Desc: "Get step-by-step guidance for real-life legal situations.",

    chatPlaceholder: "Type your legal question...",
    send: "Send",
    newChat: "New Conversation",
    conversations: "Conversations",
    noConversations: "No conversations yet",
    thinking: "Thinking...",

    email: "Email",
    password: "Password",
    fullName: "Full Name",
    loginTitle: "Login to Prohor",
    registerTitle: "Register on Prohor",
    noAccount: "Don't have an account?",
    hasAccount: "Already have an account?",

    documentsTitle: "Legal Documents",
    searchDocuments: "Search documents...",
    verified: "Verified",
    noDocuments: "No documents found",

    searchTitle: "Search Legal Information",
    searchPlaceholder: "Search laws, sections or topics...",
    searchButton: "Search",
    noResults: "No results found",

    disclaimer: "Prohor provides general legal information, not professional legal advice.",

    tagline: "Understand the Law, Know Your Rights.",
    copyright: "© 2026 Prohor. All rights reserved.",
  },
};

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => {
    return localStorage.getItem("prohor_lang") || "bn";
  });

  const t = (key) => translations[lang]?.[key] || translations.en[key] || key;

  const toggleLanguage = () => {
    const newLang = lang === "bn" ? "en" : "bn";
    setLang(newLang);
    localStorage.setItem("prohor_lang", newLang);
  };

  return (
    <LanguageContext.Provider value={{ lang, t, toggleLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
}

export const useLanguage = () => {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
};
