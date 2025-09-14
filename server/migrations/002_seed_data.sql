-- Seed data for testing the AI Chat Application
-- This file contains sample data for development and testing

-- Insert sample conversations
INSERT INTO conversations (id, title, created_at, updated_at) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'Roman Military History Discussion', '2024-01-15 10:00:00+00', '2024-01-15 10:30:00+00'),
    ('550e8400-e29b-41d4-a716-446655440002', 'Ancient Greek Warfare Analysis', '2024-01-16 14:00:00+00', '2024-01-16 14:45:00+00'),
    ('550e8400-e29b-41d4-a716-446655440003', 'Comparative Ancient Military Tactics', '2024-01-17 09:00:00+00', '2024-01-17 09:20:00+00');

-- Insert sample messages
INSERT INTO messages (id, conversation_id, role, content, timestamp, sources, agent_info) VALUES
    -- Conversation 1: Roman Military History
    ('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'user', 'Tell me about Roman legion structure and organization.', '2024-01-15 10:00:00+00', NULL, NULL),
    ('660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'assistant', 'Roman legions were highly organized military units, typically consisting of about 5,000-6,000 soldiers. Each legion was divided into 10 cohorts, with the first cohort being larger and more prestigious than the others. The basic tactical unit was the century, containing about 80-100 men led by a centurion.', '2024-01-15 10:01:00+00', 
     '[{"document_id": "770e8400-e29b-41d4-a716-446655440001", "filename": "roman_army_structure.pdf", "page": 15}]'::jsonb,
     '{"agent_type": "historian", "reasoning_steps": ["Analyzed query about Roman military", "Retrieved relevant historical information", "Synthesized response about legion structure"]}'::jsonb),
    ('660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'user', 'How did Roman military tactics evolve during the Republic?', '2024-01-15 10:15:00+00', NULL, NULL),
    ('660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', 'assistant', 'Roman military tactics evolved significantly during the Republic period. Initially influenced by Greek phalanx formations, Romans gradually developed the manipular system around the 4th century BC, which provided greater flexibility. This later evolved into the cohort system during the Marian reforms (107 BC), creating the professional legions that would dominate for centuries.', '2024-01-15 10:16:00+00',
     '[{"document_id": "770e8400-e29b-41d4-a716-446655440001", "filename": "roman_army_structure.pdf", "page": 23}, {"document_id": "770e8400-e29b-41d4-a716-446655440002", "filename": "marian_reforms.pdf", "page": 8}]'::jsonb,
     '{"agent_type": "researcher", "tools_used": ["document_search", "timeline_builder"], "reasoning_steps": ["Searched for information on Roman tactical evolution", "Built timeline of military reforms", "Synthesized historical progression"]}'::jsonb),

    -- Conversation 2: Ancient Greek Warfare
    ('660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', 'user', 'Explain the hoplite phalanx formation and its effectiveness.', '2024-01-16 14:00:00+00', NULL, NULL),
    ('660e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440002', 'assistant', 'The hoplite phalanx was a tight infantry formation where heavily armed soldiers (hoplites) stood shoulder to shoulder in ranks, typically 8 deep. Each hoplite carried a large bronze shield (hoplon), spear (dory), and sword. The formation''s strength came from collective discipline and the overlapping shields creating a "wall of bronze." It was highly effective against frontal attacks but vulnerable to flanking maneuvers.', '2024-01-16 14:02:00+00',
     '[{"document_id": "770e8400-e29b-41d4-a716-446655440003", "filename": "greek_warfare_tactics.pdf", "page": 12}]'::jsonb,
     '{"agent_type": "historian", "reasoning_steps": ["Analyzed query about Greek military tactics", "Retrieved information on phalanx formation", "Explained tactical advantages and weaknesses"]}'::jsonb),

    -- Conversation 3: Comparative Analysis
    ('660e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440003', 'user', 'Compare Roman and Greek military approaches. What were the key differences?', '2024-01-17 09:00:00+00', NULL, NULL),
    ('660e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440003', 'assistant', 'Roman and Greek military approaches differed significantly:\n\n**Greek Approach:**\n- Emphasized heavy infantry (hoplites) in rigid phalanx formations\n- Citizen-soldiers fighting for their city-state\n- Battles often decided by single decisive engagement\n- Limited tactical flexibility once engaged\n\n**Roman Approach:**\n- Flexible manipular/cohort system allowing tactical adaptation\n- Professional soldiers with standardized training and equipment\n- Combined arms approach integrating infantry, cavalry, and siege weapons\n- Strategic thinking focused on long-term conquest and occupation\n\nThe Roman system''s adaptability ultimately proved superior for building and maintaining a large empire.', '2024-01-17 09:05:00+00',
     '[{"document_id": "770e8400-e29b-41d4-a716-446655440001", "filename": "roman_army_structure.pdf", "page": 45}, {"document_id": "770e8400-e29b-41d4-a716-446655440003", "filename": "greek_warfare_tactics.pdf", "page": 67}]'::jsonb,
     '{"agent_type": "analyst", "tools_used": ["document_search", "cross_reference"], "reasoning_steps": ["Searched for Roman military information", "Searched for Greek military information", "Performed comparative analysis", "Synthesized key differences and advantages"]}'::jsonb);

-- Insert sample documents (these would represent uploaded PDFs)
INSERT INTO documents (id, filename, original_name, storage_path, public_url, mime_type, size, uploaded_at, status, chunk_count) VALUES
    ('770e8400-e29b-41d4-a716-446655440001', 'roman_army_structure_20240115.pdf', 'Roman Army Structure and Organization.pdf', 'documents/roman_army_structure_20240115.pdf', 'https://uicwlwzlnipvafraryee.supabase.co/storage/v1/object/public/documents/roman_army_structure_20240115.pdf', 'application/pdf', 2048576, '2024-01-15 09:00:00+00', 'ready', 45),
    ('770e8400-e29b-41d4-a716-446655440002', 'marian_reforms_20240115.pdf', 'The Marian Reforms and Professional Legions.pdf', 'documents/marian_reforms_20240115.pdf', 'https://uicwlwzlnipvafraryee.supabase.co/storage/v1/object/public/documents/marian_reforms_20240115.pdf', 'application/pdf', 1536000, '2024-01-15 09:30:00+00', 'ready', 32),
    ('770e8400-e29b-41d4-a716-446655440003', 'greek_warfare_20240116.pdf', 'Ancient Greek Warfare and the Phalanx.pdf', 'documents/greek_warfare_20240116.pdf', 'https://uicwlwzlnipvafraryee.supabase.co/storage/v1/object/public/documents/greek_warfare_20240116.pdf', 'application/pdf', 1843200, '2024-01-16 13:00:00+00', 'ready', 38);

-- Insert sample document chunks with proper 768-dimensional embeddings
-- Note: In production, these embeddings would be generated by the text-embedding-004 model
-- For testing, we'll use zero vectors of the correct dimension (768)
INSERT INTO document_chunks (id, document_id, content, embedding, page_number, chunk_index, metadata) VALUES
    -- Roman Army Structure document chunks
    ('880e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', 
     'The Roman legion was the basic military unit of the Roman army. A legion typically consisted of approximately 5,000 to 6,000 soldiers, organized into cohorts and centuries. The first cohort was larger and more prestigious, containing the legion''s best soldiers and the eagle standard.',
     array_fill(0, ARRAY[768])::vector,
     15, 1, '{"topic": "legion_structure", "keywords": ["legion", "cohort", "century", "soldiers"]}'::jsonb),
    
    ('880e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440001',
     'Centurions were the backbone of the Roman military hierarchy. These experienced officers commanded centuries and were responsible for training, discipline, and tactical leadership. The most senior centurion in a legion was the primus pilus, who commanded the first century of the first cohort.',
     array_fill(0, ARRAY[768])::vector,
     23, 2, '{"topic": "military_hierarchy", "keywords": ["centurion", "primus pilus", "leadership", "discipline"]}'::jsonb),

    -- Marian Reforms document chunks  
    ('880e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440002',
     'The Marian reforms of 107 BC transformed the Roman military from a citizen militia to a professional army. Gaius Marius standardized equipment, extended service terms to 25 years, and opened recruitment to the landless poor, creating career soldiers loyal to their commanders.',
     array_fill(0, ARRAY[768])::vector,
     8, 1, '{"topic": "military_reforms", "keywords": ["Marian reforms", "professional army", "Gaius Marius", "recruitment"]}'::jsonb),

    -- Greek Warfare document chunks
    ('880e8400-e29b-41d4-a716-446655440004', '770e8400-e29b-41d4-a716-446655440003',
     'The hoplite phalanx formation was the dominant tactical system in ancient Greek warfare. Hoplites, heavily armed infantry soldiers, formed tight ranks with overlapping shields and long spears. This formation was nearly impregnable from the front but vulnerable to flanking attacks.',
     array_fill(0, ARRAY[768])::vector,
     12, 1, '{"topic": "phalanx_formation", "keywords": ["hoplite", "phalanx", "shields", "spears", "formation"]}'::jsonb),

    ('880e8400-e29b-41d4-a716-446655440005', '770e8400-e29b-41d4-a716-446655440003',
     'Greek city-states relied primarily on citizen-soldiers who provided their own equipment. This system worked well for defending territory but limited the duration and scope of military campaigns. Professional armies were rare in the Greek world until the Hellenistic period.',
     array_fill(0, ARRAY[768])::vector,
     67, 2, '{"topic": "citizen_soldiers", "keywords": ["city-states", "citizen-soldiers", "equipment", "campaigns"]}'::jsonb);

-- Create a view for easy conversation retrieval with message counts
CREATE VIEW conversation_summary AS
SELECT 
    c.id,
    c.title,
    c.created_at,
    c.updated_at,
    COUNT(m.id) as message_count,
    MAX(m.timestamp) as last_message_at
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
GROUP BY c.id, c.title, c.created_at, c.updated_at;

-- Create a view for document statistics
CREATE VIEW document_stats AS
SELECT 
    d.id,
    d.filename,
    d.original_name,
    d.status,
    d.uploaded_at,
    d.size,
    d.chunk_count,
    COUNT(dc.id) as actual_chunk_count,
    AVG(LENGTH(dc.content)) as avg_chunk_length
FROM documents d
LEFT JOIN document_chunks dc ON d.id = dc.document_id
GROUP BY d.id, d.filename, d.original_name, d.status, d.uploaded_at, d.size, d.chunk_count;