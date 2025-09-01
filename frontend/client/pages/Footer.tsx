import { GraduationCap } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t bg-card/50 mt-16">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between">
          <div className="flex items-center gap-3 mb-4 md:mb-0">
            <div className="p-1.5 bg-university-blue rounded-lg">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <span className="font-medium">
              © 2024 Universidade Federal do Agreste de Pernambuco
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            Sistema RAG desenvolvido para assistência acadêmica
          </p>
        </div>
      </div>
    </footer>
  );
}
