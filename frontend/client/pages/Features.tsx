import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { BookOpen, Users } from "lucide-react";

export default function Features() {
  return (
    <section className="flex flex-wrap justify-center gap-6 mb-16">
      <Card className="w-[550px] h-[350px] flex flex-col border hover:border-university-blue/50 transition">
        <CardHeader className="pb-4">
          <div className="p-2 bg-university-blue/10 rounded-lg w-fit mb-4">
            <BookOpen className="w-6 h-6 text-university-blue" />
          </div>
          <CardTitle className="text-xl mb-2">Coordenadoria de Estágio</CardTitle>
          <CardDescription className="text-base leading-relaxed">
            Orientação de procedimentos e documentos acerca das atividades de
            Estágio Obrigatório e Não Obrigatório.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-grow flex pt-1">
          <p className="text-sm text-muted-foreground">
            Acesse informações atualizadas sobre os processos com o setor de
            Coordenadoria de Estágio.
          </p>
        </CardContent>
      </Card>

      <Card className="w-[550px] h-[350px] flex flex-col border hover:border-university-blue/50 transition">
        <CardHeader>
          <div className="p-2 bg-university-gold/10 rounded-lg w-fit mb-4">
            <Users className="w-6 h-6 text-university-gold" />
          </div>
          <CardTitle className="text-xl mb-2">DRCA</CardTitle>
          <CardDescription className="text-base leading-relaxed">
            Alteração Cadastral, desistência de Curso, solicitação do Diploma,
            tratamento Excepcional de Faltas e outras informações.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-grow flex pt-1">
          <p className="text-sm text-muted-foreground">
            Orientações completas sobre todos os processos administrativos entre em contato com o setor DRCA.
          </p>
        </CardContent>
      </Card>
    </section>
  );
}
