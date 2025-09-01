import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronDown, ChevronUp, MessageCircle } from "lucide-react";
import { faqData } from "./data";

interface Props {
  onChatClick: () => void;
}

export default function Faq({ onChatClick }: Props) {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <section className="mb-16">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold mb-4">Perguntas Frequentes</h2>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Encontre respostas rápidas para as principais dúvidas sobre nossa universidade
        </p>
      </div>

      <div className="max-w-4xl mx-auto space-y-4">
        {faqData.map((faq, index) => (
          <Card key={index} className="border hover:border-university-blue/30 transition">
            <CardHeader
              className="cursor-pointer"
              onClick={() => setOpenFaq(openFaq === index ? null : index)}
            >
              <div className="flex items-center justify-between">
                <CardTitle className="text-left text-lg font-semibold pr-4">
                  {faq.question}
                </CardTitle>
                {openFaq === index ? (
                  <ChevronUp className="w-5 h-5 text-university-blue" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                )}
              </div>
            </CardHeader>
            {openFaq === index && (
              <CardContent className="pt-0">
                <p className="text-muted-foreground leading-relaxed">{faq.answer}</p>
              </CardContent>
            )}
          </Card>
        ))}
      </div>

      <div className="text-center mt-8">
        <p className="text-muted-foreground mb-4">Não encontrou a resposta?</p>
        <button
          onClick={onChatClick}
          className="px-4 py-2 border border-university-blue text-university-blue hover:bg-university-blue hover:text-white rounded-lg transition"
        >
          <MessageCircle className="w-4 h-4 mr-2 inline" />
          Pergunte ao Assistente
        </button>
      </div>
    </section>
  );
}
