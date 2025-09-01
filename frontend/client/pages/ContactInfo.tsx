import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Phone, Mail, LinkIcon } from "lucide-react";

export default function ContactInfo() {
  return (
    <Card className="bg-gradient-to-r from-university-blue/5 to-university-navy/5 border border-university-blue/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Phone className="w-5 h-5" />
          Informações de Contato
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ContactItem
            icon={<Mail className="w-5 h-5 text-university-blue" />}
            title="E-mail da Coordenação de Estágio"
            value="estagio.preg@ufape.edu.br"
          />
          <ContactItem
            icon={<Mail className="w-5 h-5 text-university-blue" />}
            title="E-mail do DRCA"
            value="drca@ufape.edu.br"
          />
          <ContactItem
            icon={<LinkIcon className="w-5 h-5 text-university-blue" />}
            title="Para mais informações"
            links={[
              { href: "https://ufape.edu.br/drca", label: "https://ufape.edu.br/drca" },
              { href: "https://ufape.edu.br/estagio", label: "https://ufape.edu.br/estagio" },
            ]}
          />
        </div>
      </CardContent>
    </Card>
  );
}

function ContactItem({
  icon,
  title,
  value,
  links,
}: {
  icon: React.ReactNode;
  title: string;
  value?: string;
  links?: { href: string; label: string }[];
}) {
  return (
    <div className="flex flex-col items-center text-center p-4 bg-card rounded-lg border hover:border-university-blue/30 transition">
      <div className="p-2 bg-university-blue/10 rounded-lg mb-3">{icon}</div>
      <div>
        <p className="font-medium mb-1">{title}</p>
        {value && <p className="text-sm text-muted-foreground">{value}</p>}
        {links &&
          links.map((link, idx) => (
            <p key={idx} className="text-sm text-muted-foreground">
              <a
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-university-blue hover:underline"
              >
                {link.label}
              </a>
            </p>
          ))}
      </div>
    </div>
  );
}
