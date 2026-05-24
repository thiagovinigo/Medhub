import React from 'react';
import { ArrowLeft, ArrowRight, Search } from 'lucide-react';

// Patient-facing specialty cards — language is for the citizen, not the doctor
export const SPECIALTY_CARDS = [
  {
    key: 'spine',
    label: 'Coluna e Costas',
    description: 'Dor nas costas, hérnia de disco, ciática, dor no pescoço',
    color: '#3b82f6',
    bg: 'rgba(59,130,246,0.08)',
    border: 'rgba(59,130,246,0.25)',
    emoji: '🦴',
    tier: 1,
    suggestedModality: 'MR',
    suggestedExams: ['RM Coluna Cervical', 'RM Coluna Lombar', 'RX Coluna'],
    uploadHint: 'Imagens da RM ou TC + pedido médico',
    complaintHint: 'Ex: Dor nas costas que irradia para a perna há 3 meses',
  },
  {
    key: 'msk',
    label: 'Ossos e Articulações',
    description: 'Joelho, ombro, quadril, tornozelo — dor, fratura ou lesão',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.08)',
    border: 'rgba(245,158,11,0.25)',
    emoji: '🦵',
    tier: 1,
    suggestedModality: 'MR',
    suggestedExams: ['RM Joelho', 'RM Ombro', 'RX Quadril', 'RM Tornozelo'],
    uploadHint: 'Imagens da RM ou RX da articulação',
    complaintHint: 'Ex: Dor no joelho direito ao subir escada após queda',
  },
  {
    key: 'thorax',
    label: 'Pulmões e Tórax',
    description: 'Falta de ar, tosse, nódulo pulmonar, pneumonia',
    color: '#06b6d4',
    bg: 'rgba(6,182,212,0.08)',
    border: 'rgba(6,182,212,0.25)',
    emoji: '🫁',
    tier: 1,
    suggestedModality: 'CT',
    suggestedExams: ['TC de Tórax', 'RX de Tórax', 'TC de Alta Resolução'],
    uploadHint: 'TC ou RX de tórax + laudo do médico',
    complaintHint: 'Ex: Nódulo pulmonar encontrado em TC de rotina',
  },
  {
    key: 'neuro',
    label: 'Cabeça e Neurologia',
    description: 'Dor de cabeça, tontura, AVC, epilepsia, tumor cerebral',
    color: '#8b5cf6',
    bg: 'rgba(139,92,246,0.08)',
    border: 'rgba(139,92,246,0.25)',
    emoji: '🧠',
    tier: 2,
    suggestedModality: 'MR',
    suggestedExams: ['RM de Crânio', 'TC de Crânio', 'RM do Encéfalo'],
    uploadHint: 'RM ou TC do crânio/encéfalo',
    complaintHint: 'Ex: Dores de cabeça frequentes, médico pediu RM',
  },
  {
    key: 'abdomen',
    label: 'Barriga e Digestivo',
    description: 'Fígado, vesícula, rim, pâncreas, dor abdominal',
    color: '#10b981',
    bg: 'rgba(16,185,129,0.08)',
    border: 'rgba(16,185,129,0.25)',
    emoji: '🫀',
    tier: 2,
    suggestedModality: 'CT',
    suggestedExams: ['TC de Abdômen', 'US Abdominal', 'TC Abdômen e Pelve'],
    uploadHint: 'TC, RM ou ultrassom abdominal',
    complaintHint: 'Ex: Dor no lado direito, médico encontrou cálculos',
  },
  {
    key: 'cardio',
    label: 'Coração e Vasos',
    description: 'Dor no peito, palpitação, pressão alta, coronárias',
    color: '#ef4444',
    bg: 'rgba(239,68,68,0.08)',
    border: 'rgba(239,68,68,0.25)',
    emoji: '❤️',
    tier: 2,
    suggestedModality: 'CT',
    suggestedExams: ['TC Coronária', 'Ecocardiograma', 'Cintilografia Miocárdica'],
    uploadHint: 'TC coronária, ecocardiograma ou cintilografia',
    complaintHint: 'Ex: Dor no peito aos esforços, ECG alterado',
  },
  {
    key: 'breast',
    label: 'Mama',
    description: 'Mamografia, nódulo na mama, BI-RADS, acompanhamento',
    color: '#ec4899',
    bg: 'rgba(236,72,153,0.08)',
    border: 'rgba(236,72,153,0.25)',
    emoji: '🩷',
    tier: 2,
    suggestedModality: 'XR',
    suggestedExams: ['Mamografia Bilateral', 'US de Mama', 'RM de Mamas'],
    uploadHint: 'Mamografia + laudo (fundamental para comparar BI-RADS)',
    complaintHint: 'Ex: Mamografia com resultado BI-RADS 4, médico pediu biópsia',
  },
  {
    key: 'endocrino',
    label: 'Hormônios e Tireoide',
    description: 'Nódulo na tireoide, exames hormonais, diabetes, adrenal',
    color: '#f97316',
    bg: 'rgba(249,115,22,0.08)',
    border: 'rgba(249,115,22,0.25)',
    emoji: '⚡',
    tier: 3,
    suggestedModality: 'US',
    suggestedExams: ['US de Tireoide', 'RM de Hipófise', 'TC de Adrenais'],
    uploadHint: 'Ultrassom da tireoide + exames de sangue (TSH, T4)',
    complaintHint: 'Ex: Nódulo encontrado na tireoide, médico pediu PAAF',
  },
  {
    key: 'onco',
    label: 'Oncologia',
    description: 'Tumor, metástase, estadiamento, PET-CT, segunda opinião',
    color: '#6366f1',
    bg: 'rgba(99,102,241,0.08)',
    border: 'rgba(99,102,241,0.25)',
    emoji: '🔬',
    tier: 3,
    suggestedModality: 'PET',
    suggestedExams: ['PET-CT', 'TC Estadiamento', 'RM Corpo Inteiro'],
    uploadHint: 'PET-CT, TC de estadiamento + laudo da biópsia',
    complaintHint: 'Ex: Diagnóstico de tumor, quero entender o estadiamento',
  },
  {
    key: 'nutri',
    label: 'Nutrição e Metabolismo',
    description: 'Colesterol, glicemia, hemograma, vitaminas, peso e dieta',
    color: '#22c55e',
    bg: 'rgba(34,197,94,0.08)',
    border: 'rgba(34,197,94,0.25)',
    emoji: '🥗',
    tier: 3,
    suggestedModality: 'Outro',
    suggestedExams: ['Hemograma Completo', 'Perfil Lipídico', 'Glicemia de Jejum', 'TSH / T4'],
    uploadHint: 'Resultados de exames de sangue (PDF ou foto)',
    complaintHint: 'Ex: Colesterol alto, médico sugeriu mudar alimentação',
  },
];

export default function SpecialtyDashboard({ patient, onSelect, onBack }) {
  const tier1 = SPECIALTY_CARDS.filter(c => c.tier === 1);
  const tier2 = SPECIALTY_CARDS.filter(c => c.tier === 2);
  const tier3 = SPECIALTY_CARDS.filter(c => c.tier === 3);

  const Card = ({ card }) => (
    <div
      className="specialty-card"
      style={{ '--card-color': card.color, '--card-bg': card.bg, '--card-border': card.border }}
      onClick={() => onSelect(card)}
    >
      <div className="specialty-card-emoji">{card.emoji}</div>
      <div className="specialty-card-body">
        <div className="specialty-card-label">{card.label}</div>
        <div className="specialty-card-desc">{card.description}</div>
      </div>
      <ArrowRight size={16} className="specialty-card-arrow" />
    </div>
  );

  return (
    <div className="specialty-dashboard">
      <div className="specialty-dash-header">
        <button className="icon-btn" onClick={onBack}><ArrowLeft size={18} /></button>
        <div>
          <h2 className="wizard-title">Segunda Opinião com IA</h2>
          <div className="wizard-subtitle">
            {patient?.name ? `Para ${patient.name} — ` : ''}Escolha a área do seu exame
          </div>
        </div>
      </div>

      <div className="specialty-dash-body">
        <p className="specialty-dash-intro">
          Selecione a especialidade do exame ou consulta que você quer entender melhor.
          A IA vai analisar suas imagens e documentos e te dar uma explicação clara.
        </p>

        {tier1.length > 0 && (
          <div className="specialty-group">
            <div className="specialty-group-label">Mais comuns</div>
            <div className="specialty-grid">
              {tier1.map(c => <Card key={c.key} card={c} />)}
            </div>
          </div>
        )}

        {tier2.length > 0 && (
          <div className="specialty-group">
            <div className="specialty-group-label">Outras especialidades</div>
            <div className="specialty-grid">
              {tier2.map(c => <Card key={c.key} card={c} />)}
            </div>
          </div>
        )}

        {tier3.length > 0 && (
          <div className="specialty-group">
            <div className="specialty-grid">
              {tier3.map(c => <Card key={c.key} card={c} />)}
            </div>
          </div>
        )}

        <div className="specialty-group">
          <div
            className="specialty-card specialty-card-general"
            onClick={() => onSelect(null)}
          >
            <Search size={22} style={{ color: '#64748b', flexShrink: 0 }} />
            <div className="specialty-card-body">
              <div className="specialty-card-label">Não sei / Análise Geral</div>
              <div className="specialty-card-desc">A IA detecta automaticamente a especialidade pelo tipo de exame</div>
            </div>
            <ArrowRight size={16} className="specialty-card-arrow" />
          </div>
        </div>
      </div>
    </div>
  );
}
