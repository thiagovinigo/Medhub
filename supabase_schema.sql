-- Criar tabela de análises
create table public.analyses (
  id uuid default gen_random_uuid() primary key,
  image_url text not null,
  analysis_text text not null,
  research_text text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Ativar Row Level Security (RLS)
alter table public.analyses enable row level security;

-- Permitir leitura e inserção públicas (já que ainda não temos login)
create policy "Permitir leitura pública" on public.analyses for select using (true);
create policy "Permitir inserção pública" on public.analyses for insert with check (true);

-- Criar Bucket público para as imagens
insert into storage.buckets (id, name, public) 
values ('medical-images', 'medical-images', true);

-- Políticas de Storage para o Bucket medical-images
create policy "Permitir visualização pública de imagens"
  on storage.objects for select
  using ( bucket_id = 'medical-images' );

create policy "Permitir upload público de imagens"
  on storage.objects for insert
  with check ( bucket_id = 'medical-images' );
