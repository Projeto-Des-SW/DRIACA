import { Sparkles, MessageCircle } from "lucide-react";

interface HeroProps {
  onChatClick: () => void;
}

export default function Hero({ onChatClick }: HeroProps) {
  return (
    <section className="text-center mb-16">
      <div className="flex justify-center mb-6">
        <div className="p-4 bg-gradient-to-br from-university-blue to-university-blue-dark rounded-2xl shadow-lg">
          <Sparkles className="w-12 h-12 text-white" />
        </div>
      </div>

      <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-university-blue to-university-navy bg-clip-text text-transparent">
        Assistente Acadêmico
      </h1>

      <p className="text-xl text-muted-foreground mb-8 w-full max-w-4xl mx-auto">
        Sistema RAG inteligente para responder suas dúvidas sobre o DRCA e o
        setor de estágio. Pergunte sobre serviços realizados, aproveitamento de
        disciplina, matrícula e muito mais!
      </p>

      <button
        onClick={onChatClick}
        className="bg-university-blue hover:bg-university-blue-dark text-white px-8 py-6 text-lg rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center mx-auto"
      >
        <MessageCircle className="w-6 h-6 mr-2" />
        Iniciar Conversa
      </button>
    </section>
  );
}
