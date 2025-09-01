import { useState } from "react";
import { ChatBot } from "@/components/ChatBot";

import Header from "./Header";
import Hero from "./Hero";
import Features from "./Features";
import Faq from "./Faq";
import ContactInfo from "./ContactInfo";
import Footer from "./Footer";
import FloatingChatButton from "@/components/FloatingChatButton";

export default function Index() {
  const [showChat, setShowChat] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-university-blue/5">
      <Header setShowChat={setShowChat} />

      {showChat ? (
        <section className="container mx-auto px-4 py-6 h-[calc(100vh-80px)]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Chat Assistente Acadêmico</h2>
            <button
              onClick={() => setShowChat(false)}
              className="px-4 py-2 border border-university-blue text-university-blue hover:bg-university-blue hover:text-white rounded-lg transition"
            >
              Voltar ao Início
            </button>
          </div>
          <div className="h-[calc(100%-4rem)]">
            <ChatBot />
          </div>
        </section>
      ) : (
        <main className="container mx-auto px-4 py-12">
          <Hero onChatClick={() => setShowChat(true)} />
          <Features />
          <FloatingChatButton onChatClick={() => setShowChat(true)} />
          <Faq onChatClick={() => setShowChat(true)} />
          <ContactInfo />
        </main>
      )}

      <Footer />
    </div>
  );
}
