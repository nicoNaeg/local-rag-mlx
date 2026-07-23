from dataclasses import dataclass, field
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from local_rag.config import Settings


@dataclass(frozen=True)
class Section:
    heading: str
    paragraphs: list[str]
    table: list[list[str]] | None = None


@dataclass(frozen=True)
class Doc:
    filename: str
    title: str
    subtitle: str
    sections: list[Section] = field(default_factory=list)


DOCS: list[Doc] = [
    Doc(
        filename="manuel_rh.pdf",
        title="Manuel des ressources humaines",
        subtitle="Solencia SAS. Version 4.2, janvier 2026. Direction des ressources humaines: Claire Fontaine.",
        sections=[
            Section(
                "Objet et champ d'application",
                [
                    "Ce manuel s'applique a l'ensemble des collaborateurs de Solencia SAS: salaries en CDI et CDD, alternants et stagiaires. Solencia compte 214 collaborateurs repartis entre le siege de Nantes et les agences de Lyon et Toulouse.",
                    "Il complete le reglement interieur et la convention collective Syntec. En cas de contradiction, la convention collective prevaut.",
                ],
            ),
            Section(
                "Temps de travail",
                [
                    "La duree de travail de reference est de 37 heures 30 par semaine pour les non-cadres, avec des horaires souples autour d'une plage fixe de 9h30 a 16h00.",
                    "Les cadres autonomes relevent d'un forfait annuel de 216 jours travailles. Le suivi de la charge est aborde a chaque entretien annuel.",
                ],
            ),
            Section(
                "Conges payes et RTT",
                [
                    "Chaque collaborateur acquiert 25 jours ouvres de conges payes par an, auxquels s'ajoutent 12 jours de RTT pour les salaries a 37h30.",
                    "Les demandes se font dans Payfit et doivent etre validees par le manager sous 5 jours ouvres. Les conges non pris peuvent etre reportes jusqu'au 31 mars de l'annee suivante, au-dela ils sont perdus.",
                ],
            ),
            Section(
                "Teletravail",
                [
                    "Le teletravail est ouvert a tous les postes compatibles apres validation de la periode d'essai, dans la limite de 3 jours par semaine. Le mardi est une journee de presence obligatoire en equipe.",
                    "Une indemnite de 2,60 EUR par jour teletravaille est versee, plafonnee a 55 EUR par mois. Le teletravail fait l'objet d'un avenant au contrat de travail, reversible avec un preavis d'un mois de part et d'autre.",
                ],
            ),
            Section(
                "Remuneration et avantages",
                [
                    "La paie est versee le 28 de chaque mois. Une prime vacances equivalente a 1% de la masse salariale est repartie entre les salaries presents au 31 mai, conformement a la convention Syntec.",
                    "Les titres-restaurant ont une valeur faciale de 11,50 EUR, pris en charge a 60% par l'employeur. Un accord d'interessement est en vigueur depuis 2024.",
                ],
            ),
            Section(
                "Mutuelle et prevoyance",
                [
                    "La couverture sante est assuree par le contrat collectif Alan Blue, finance a 62% par l'employeur. L'affiliation est obligatoire sauf cas de dispense legale, les ayants droit peuvent etre ajoutes a la charge du salarie.",
                    "Un contrat de prevoyance couvre les risques incapacite, invalidite et deces des la date d'embauche.",
                ],
            ),
            Section(
                "Formation",
                [
                    "Chaque collaborateur dispose d'un budget formation de 1 800 EUR par an, hors CPF. Les demandes sont a deposer au premier trimestre aupres du manager, qui arbitre avec la RH.",
                    "Le catalogue interne Solencia Academy propose des parcours produit, vente et management. Les formations obligatoires (securite, RGPD) ne sont pas imputees sur le budget individuel.",
                ],
            ),
            Section(
                "Entretiens et evaluation",
                [
                    "L'entretien annuel a lieu chaque annee en janvier et fixe les objectifs de l'annee. L'entretien professionnel, centre sur le parcours, est organise tous les deux ans.",
                    "Une people review reunit chaque mois de juin les managers et la RH pour les sujets de mobilite et d'evolution salariale.",
                ],
            ),
            Section(
                "Absences et maladie",
                [
                    "En cas d'absence imprevue, le collaborateur previent son manager avant 9h30 et transmet son arret de travail sous 48 heures a rh@solencia.fr.",
                    "Solencia pratique la subrogation: le salaire est maintenu a 100% pendant 90 jours pour les salaries ayant plus d'un an d'anciennete.",
                ],
            ),
            Section(
                "Depart de l'entreprise",
                [
                    "Les preavis applicables sont ceux de la convention Syntec: 3 mois pour les cadres, 1 a 2 mois pour les non-cadres selon l'anciennete.",
                    "Le materiel est restitue au plus tard le dernier jour travaille. Un entretien d'offboarding est propose par la RH, et l'acces aux comptes est revoque le jour du depart a 18h00.",
                ],
            ),
        ],
    ),
    Doc(
        filename="politique_securite.pdf",
        title="Politique de securite des systemes d'information",
        subtitle="PSSI Solencia. Version 3.1, mars 2026. RSSI: Karim Haddad.",
        sections=[
            Section(
                "Portee",
                [
                    "La PSSI s'applique aux collaborateurs, prestataires et stagiaires qui accedent au systeme d'information de Solencia, quel que soit le materiel utilise.",
                    "Toute exception doit etre validee par ecrit par le RSSI et revue tous les six mois.",
                ],
            ),
            Section(
                "Classification des donnees",
                [
                    "Les donnees sont classees en quatre niveaux: C0 publique, C1 interne, C2 confidentielle, C3 restreinte.",
                    "Les donnees C2 ne peuvent etre partagees qu'avec des tiers sous accord de confidentialite. Les donnees C3 (paie, donnees clients nominatives, secrets industriels) sont chiffrees au repos et leur partage hors du coffre numerique est interdit.",
                ],
            ),
            Section(
                "Mots de passe",
                [
                    "Les mots de passe comportent au minimum 16 caracteres. L'usage du gestionnaire Vaultwarden fourni par l'entreprise est obligatoire, et un mot de passe ne doit jamais etre reutilise entre services.",
                    "La rotation periodique n'est pas exigee: un mot de passe n'est change qu'en cas de suspicion de compromission.",
                ],
            ),
            Section(
                "Authentification multifacteur",
                [
                    "Le MFA est obligatoire sur Google Workspace, GitLab, le VPN et Payfit. Les facteurs acceptes sont les applications TOTP et les cles FIDO2.",
                    "La validation par SMS est interdite car vulnerable au SIM swapping.",
                ],
            ),
            Section(
                "Postes de travail",
                [
                    "Tous les postes sont chiffres (FileVault sur macOS, BitLocker sur Windows, LUKS sur Linux) et verrouilles automatiquement apres 5 minutes d'inactivite.",
                    "Les mises a jour de securite sont appliquees sous 7 jours. L'agent EDR CrowdStrike est deploye sur l'ensemble du parc et ne doit jamais etre desactive.",
                ],
            ),
            Section(
                "Acces distant",
                [
                    "Hors des locaux, l'acces aux ressources internes et aux donnees C2 ou superieures passe obligatoirement par le VPN WireGuard de l'entreprise, avec le split tunneling desactive.",
                    "L'usage d'un wifi public sans VPN est proscrit pour toute activite professionnelle.",
                ],
            ),
            Section(
                "Messagerie et hameconnage",
                [
                    "Avant tout clic, verifier l'adresse reelle de l'expediteur et la coherence de la demande. Ne jamais saisir ses identifiants depuis un lien recu par mail.",
                    "Les messages suspects sont signales via le bouton Signaler de Gmail. Des campagnes de faux hameconnage sont menees chaque trimestre a des fins de sensibilisation.",
                ],
            ),
            Section(
                "Gestion des incidents",
                [
                    "Tout incident de securite avere ou suspecte est declare sous 4 heures ouvrees a security@solencia.fr ou sur le canal Slack #sec-incidents.",
                    "En cas de machine compromise: ne pas l'eteindre, la deconnecter du reseau et attendre les instructions de l'equipe securite. Les preuves (mails, captures) sont conservees.",
                ],
            ),
            Section(
                "Sauvegardes",
                [
                    "La strategie suit la regle 3-2-1: trois copies, deux supports, une copie hors site. Les donnees de production Helios font l'objet de snapshots horaires.",
                    "Des tests de restauration sont realises chaque semestre et leurs resultats presentes en comite securite.",
                ],
            ),
            Section(
                "Sanctions",
                [
                    "Le non-respect de la PSSI expose le collaborateur aux sanctions disciplinaires prevues au reglement interieur, sans prejudice d'eventuelles poursuites.",
                ],
            ),
        ],
    ),
    Doc(
        filename="guide_onboarding.pdf",
        title="Guide d'accueil des nouveaux collaborateurs",
        subtitle="Solencia SAS. Version 2.5, fevrier 2026. Office manager: Lucie Bernard.",
        sections=[
            Section(
                "Bienvenue chez Solencia",
                [
                    "Solencia concoit Helios, une plateforme de supervision de centrales solaires utilisee par plus de 1 200 sites en Europe. L'entreprise est organisee en trois directions: Produit, Operations et Commerce.",
                    "Nos engagements: fiabilite des donnees, sobriete energetique et transparence avec nos clients.",
                ],
            ),
            Section(
                "Avant votre arrivee",
                [
                    "Le contrat est signe electroniquement via Docusign. Vous choisissez votre materiel dans le formulaire d'accueil: MacBook Pro 14 pouces ou Dell XPS 13 sous Ubuntu.",
                    "Le formulaire d'affiliation a la mutuelle Alan et le RIB sont a retourner au moins une semaine avant le premier jour.",
                ],
            ),
            Section(
                "Votre premiere journee",
                [
                    "Accueil a 9h15 par l'office manager: remise du badge et du materiel, tour des locaux, presentation des equipes. Le dejeuner du premier jour est offert avec votre equipe.",
                    "L'apres-midi est consacre a la configuration du poste avec le support IT et a la signature des chartes (informatique, teletravail).",
                ],
            ),
            Section(
                "Comptes et outils",
                [
                    "Les comptes crees a l'arrivee: Google Workspace, Slack (rejoindre #general et #annonces), Notion (espace Solencia Hub) et Payfit.",
                    "L'acces GitLab est demande par le manager selon le poste. Toute demande d'outil supplementaire passe par it-support@solencia.fr, avec un delai de traitement de 4 heures ouvrees.",
                ],
            ),
            Section(
                "Parrainage",
                [
                    "Chaque nouvel arrivant se voit attribuer un parrain ou une marraine hors de son equipe directe, pour un point hebdomadaire de 30 minutes pendant les deux premiers mois.",
                    "Le parrain repond aux questions du quotidien et facilite la decouverte des autres equipes.",
                ],
            ),
            Section(
                "Votre premier mois",
                [
                    "La formation produit Helios se deroule sur deux demi-journees pendant les deux premieres semaines. Le module e-learning securite est obligatoire sous 15 jours.",
                    "Les objectifs de la periode d'essai sont formalises avec le manager a J+30.",
                ],
            ),
            Section(
                "Points de suivi",
                [
                    "Trois points jalonnent l'integration: J+7 avec l'office manager, J+30 et J+90 avec la RH et le manager.",
                    "Un rapport d'etonnement est demande a J+60: il alimente l'amelioration continue du parcours d'accueil.",
                ],
            ),
            Section(
                "Periode d'essai",
                [
                    "La periode d'essai est de 4 mois pour les cadres et de 2 mois pour les non-cadres, renouvelable une fois par accord ecrit des deux parties.",
                ],
            ),
            Section(
                "Contacts utiles",
                [
                    "RH: rh@solencia.fr. Support informatique: it-support@solencia.fr. Securite: security@solencia.fr. Office manager Nantes: poste 102.",
                ],
            ),
        ],
    ),
    Doc(
        filename="notes_de_frais.pdf",
        title="Procedure notes de frais et deplacements",
        subtitle="Solencia SAS. Version 3.0, janvier 2026. Direction administrative et financiere.",
        sections=[
            Section(
                "Principes",
                [
                    "Sont remboursables les frais reels engages dans l'interet de l'entreprise, accompagnes d'un justificatif. Les notes de frais sont saisies dans le module Depenses de Payfit.",
                    "Toute depense sans justificatif est refusee, sauf tolerance pour les pourboires et parcmetres inferieurs a 5 EUR.",
                ],
            ),
            Section(
                "Delais",
                [
                    "Les notes de frais sont soumises sous 30 jours calendaires apres la depense. Le manager valide sous 7 jours et le remboursement intervient sur la paie suivante.",
                    "Au-dela de 90 jours, la depense est refusee sauf accord ecrit de la DAF.",
                ],
            ),
            Section(
                "Plafonds de remboursement",
                [
                    "Les plafonds ci-dessous s'entendent par personne, justificatif obligatoire dans tous les cas.",
                ],
                table=[
                    ["Type de depense", "Plafond", "Condition"],
                    ["Repas individuel", "22 EUR", "Deplacement professionnel"],
                    ["Repas client", "38 EUR / personne", "Noms des invites requis"],
                    ["Hotel province", "130 EUR / nuit", "Petit-dejeuner inclus"],
                    ["Hotel Paris", "185 EUR / nuit", "Petit-dejeuner inclus"],
                    ["Petit-dejeuner seul", "12 EUR", "Si non inclus a l'hotel"],
                ],
            ),
            Section(
                "Deplacements",
                [
                    "Le train en seconde classe est le mode par defaut, la premiere classe est autorisee au-dela de 3 heures de trajet. L'avion n'est envisage que si le trajet en train depasse 5 heures.",
                    "Les reservations passent par TravelPerk, idealement 7 jours avant le depart pour maitriser les couts.",
                ],
            ),
            Section(
                "Vehicule personnel",
                [
                    "L'usage du vehicule personnel requiert l'autorisation prealable du manager et une assurance couvrant les deplacements professionnels.",
                    "L'indemnite kilometrique interne est de 0,52 EUR par kilometre, peages et parking rembourses sur justificatif.",
                ],
            ),
            Section(
                "Avances sur frais",
                [
                    "Une avance peut etre demandee lorsque les frais previsionnels depassent 400 EUR, au moins 10 jours avant le deplacement.",
                    "La regularisation intervient sous 15 jours apres le retour, tout trop-percu est reverse.",
                ],
            ),
            Section(
                "Depenses non remboursables",
                [
                    "Ne sont jamais rembourses: amendes et contraventions, minibar, surclassements non valides, achats personnels, ainsi que les pourboires au-dela de 5% de l'addition.",
                ],
            ),
            Section(
                "Cartes affaires",
                [
                    "Les commerciaux et les membres du comite de direction peuvent disposer d'une carte affaires, plafonnee a 2 500 EUR par mois.",
                    "Le releve mensuel est pointe dans Payfit sous 10 jours, les memes regles de justificatifs s'appliquent.",
                ],
            ),
        ],
    ),
    Doc(
        filename="spec_helios.pdf",
        title="Helios, presentation technique de la plateforme",
        subtitle="Documentation produit Solencia. Version 3.8, avril 2026. Diffusion C1 interne.",
        sections=[
            Section(
                "Vue d'ensemble",
                [
                    "Helios supervise 1 240 centrales photovoltaiques en Europe. La plateforme collecte la telemetrie des onduleurs et des capteurs meteo, detecte les anomalies de production et notifie les exploitants.",
                    "Les clients accedent aux donnees via une console web et une API REST.",
                ],
            ),
            Section(
                "Architecture",
                [
                    "Les capteurs communiquent en LoRaWAN avec la passerelle Helios Edge, un boitier ARM installe sur site capable de fonctionner 72 heures en mode deconnecte grace a son buffer local.",
                    "Les passerelles publient en MQTT vers la couche d'ingestion, qui alimente le stockage de series temporelles et l'API REST v3.",
                ],
            ),
            Section(
                "Modele de donnees",
                [
                    "Le modele repose sur trois entites: sites, equipements et series temporelles. Les mesures sont echantillonnees toutes les 10 minutes.",
                    "La granularite brute est conservee 13 mois, les agregats horaires et journaliers sont conserves 5 ans.",
                ],
            ),
            Section(
                "Seuils d'alerte par defaut",
                [
                    "Les seuils sont personnalisables par site, les valeurs par defaut sont les suivantes.",
                ],
                table=[
                    ["Metrique", "Seuil", "Severite"],
                    ["Ecart de production vs attendu", "> 12%", "Warning"],
                    ["Ecart de production vs attendu", "> 25%", "Critical"],
                    ["Temperature onduleur", "> 65 degres C", "Warning"],
                    ["Temperature onduleur", "> 80 degres C", "Critical"],
                    ["Perte de communication", "> 30 minutes", "Critical"],
                ],
            ),
            Section(
                "API",
                [
                    "L'API s'authentifie en OAuth2 client credentials. Le quota standard est de 600 requetes par minute et par client, avec pagination par curseur.",
                    "Endpoints principaux: /sites, /assets, /timeseries, /alerts. Les webhooks d'alerte sont signes HMAC SHA-256.",
                ],
            ),
            Section(
                "Disponibilite",
                [
                    "Le SLA contractuel est de 99,5% de disponibilite mensuelle, hors fenetre de maintenance planifiee le mardi de 22h00 a minuit.",
                    "Les objectifs de reprise sont un RPO de 1 heure et un RTO de 4 heures.",
                ],
            ),
            Section(
                "Securite",
                [
                    "Les donnees Helios sont classees C2. Chiffrement TLS 1.3 en transit et AES-256 au repos. L'hebergement est assure par OVHcloud a Gravelines, region eu-west-sbg.",
                    "Les journaux d'acces sont conserves 12 mois.",
                ],
            ),
            Section(
                "Versions et support",
                [
                    "La version courante est la 3.8. La version N-1 reste supportee 12 mois apres chaque sortie majeure.",
                    "Les depreciations d'API sont annoncees au moins 6 mois a l'avance dans le changelog public.",
                ],
            ),
        ],
    ),
    Doc(
        filename="procedure_achats.pdf",
        title="Procedure achats et engagement de depenses",
        subtitle="Solencia SAS. Version 2.2, mars 2026. Direction administrative et financiere.",
        sections=[
            Section(
                "Champ d'application",
                [
                    "Cette procedure couvre tout achat de biens ou de services pour le compte de Solencia. Les frais de deplacement releve de la procedure notes de frais dediee.",
                ],
            ),
            Section(
                "Seuils de validation",
                [
                    "Moins de 500 EUR HT: validation du manager. De 500 a 5 000 EUR HT: validation de la direction de BU. Au-dela de 5 000 EUR HT: validation DAF avec mise en concurrence de 3 devis.",
                    "Au-dela de 25 000 EUR HT, le comite d'engagement se prononce, avec un dossier presentant le besoin, les offres et les criteres de choix.",
                ],
            ),
            Section(
                "Demande d'achat",
                [
                    "Toute demande passe par le formulaire Achats de Notion, qui genere un numero de DA. La comptabilite emet ensuite le bon de commande.",
                    "Aucune commande orale ou par simple mail n'engage l'entreprise.",
                ],
            ),
            Section(
                "Fournisseurs",
                [
                    "Un nouveau fournisseur est reference avant toute commande: KBIS, RIB et attestation URSSAF de moins de 6 mois.",
                    "Les fournisseurs critiques sont revus une fois par an. A prestation equivalente, les fournisseurs etablis dans l'Union europeenne sont privilegies.",
                ],
            ),
            Section(
                "Reception et paiement",
                [
                    "La reception est confirmee dans l'outil par le demandeur, condition du paiement. Les factures sont reglees a 30 jours fin de mois.",
                    "Tout litige de facturation est signale a la comptabilite sous 5 jours ouvres.",
                ],
            ),
            Section(
                "Logiciels et SaaS",
                [
                    "Tout nouvel outil logiciel requiert une validation IT prealable couvrant la securite et la conformite RGPD, puis une inscription au registre des traitements le cas echeant.",
                    "Les renouvellements de licences sont revus 60 jours avant echeance pour permettre une renegociation ou une resiliation.",
                ],
            ),
            Section(
                "Urgences",
                [
                    "En cas d'urgence operationnelle, une procedure acceleree permet un accord DAF sous 24 heures, avec regularisation documentaire sous 5 jours.",
                ],
            ),
        ],
    ),
]


class _Pdf(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(
            0,
            10,
            f"Solencia (societe fictive, document de demonstration) - page {self.page_no()}",
            align="C",
        )


def _para(pdf: FPDF, height: float, text: str) -> None:
    pdf.multi_cell(0, height, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def render(doc: Doc, out_dir: Path) -> Path:
    pdf = _Pdf()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("helvetica", "B", 20)
    _para(pdf, 10, doc.title)
    pdf.set_font("helvetica", "I", 10)
    _para(pdf, 6, doc.subtitle)
    pdf.ln(6)

    for index, section in enumerate(doc.sections, start=1):
        pdf.set_font("helvetica", "B", 13)
        _para(pdf, 8, f"{index}. {section.heading}")
        pdf.ln(1)
        pdf.set_font("helvetica", "", 10.5)
        for paragraph in section.paragraphs:
            _para(pdf, 5.5, paragraph)
            pdf.ln(2)
        if section.table:
            _render_table(pdf, section.table)
            pdf.ln(2)
        pdf.ln(3)

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / doc.filename
    pdf.output(str(path))
    return path


def _render_table(pdf: FPDF, rows: list[list[str]]) -> None:
    width = pdf.epw / len(rows[0])
    pdf.set_font("helvetica", "B", 9.5)
    for row_index, row in enumerate(rows):
        for cell in row:
            pdf.cell(width, 7, cell, border=1)
        pdf.ln(7)
        if row_index == 0:
            pdf.set_font("helvetica", "", 9.5)


def main() -> None:
    settings = Settings()
    for doc in DOCS:
        path = render(doc, settings.corpus_dir)
        print(f"Wrote {path}")
    print(f"{len(DOCS)} documents in {settings.corpus_dir}")


if __name__ == "__main__":
    main()
