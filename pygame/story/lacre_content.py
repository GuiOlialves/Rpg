"""Authored dungeon content; identities and evidence remain independent of presentation."""
REGIONS=('inscription_vestibule','echo_gallery','forbidden_archive','guardian_chamber','seal_core')
NAMES=('Vestíbulo das Inscrições','Galeria dos Ecos','Arquivo Interditado','Câmara dos Guardiões','Núcleo do Lacre')
ENTER_FLAGS={r:'lacre_'+r+'_entered' for r in REGIONS}
COUNTS=(2,3,2,1,1)
FLAGS=tuple(ENTER_FLAGS.values())+tuple('lacre_'+s for s in (
    'vestige_seen','vestibule_step1','vestibule_step2','vestibule_open',
    'gallery_door_seen','gallery_hand_seen','gallery_seal_seen','gallery_step1','gallery_step2','gallery_open',
    'purpose_found','military_found','identity_found','archive_open','secret_seen','secret_open','cache_found','lore_found','shortcut_open',
    'vigia_defeated','checkpoint_found','core_vista_seen','custodian_talk_seen','boss_wounded','boss_phase2_seen',
    'anchor_left_broken','anchor_right_broken','custodian_defeated','aftermath_seen','first_found','second_found','memory_seen',
    'records_ready','choice_preserved','choice_shared','reward_given','lead_found','return_seen','final_seen'))
DEFEATS=tuple(f'c2_{r}_enemy_{i}_defeated' for r,n in zip(REGIONS,COUNTS) for i in range(n))
DOCUMENTS={
 'lacre_purpose':('A função da Câmara', 'lacre_purpose_found',
   ('Estatuto de custódia. Conservar testemunhos sem os entregar à autoridade que requisitou sua guarda.',
    'O lacre isola o acesso à lembrança; não destrói seu vestígio. Perda de orientação e falhas entre nomes e rostos foram registradas.',
    'Reabrir um rol expõe pessoas, não apenas informações. Cada abertura exige cotejar a autorização com o original.')),
 'lacre_military':('Requisições das escoltas','lacre_military_found',
   ('Duas requisições. A vermelha pede o depoimento de portadores da remessa N-04. A azul pede a relação de acolhidos.',
    'Ambas foram negadas. Depois, a margem registra um interrogatório sob autorização militar, sem a presença do depositante.',
    'A Câmara preservava testemunhos. Também podia impedir que alguém respondesse. Os mesmos fechos serviam às duas coisas.')),
 'lacre_identity':('Ficha de admissão R-17','lacre_identity_found',
   ('Admissão: identificação pessoal R-17, cruzada com a segunda via N-04, gaveta 7 do Posto Norte.',
    'O desenho da peça tem a mesma falha no aro da minha identificação. A ficha conserva sua impressão, não apenas o número.',
    'Pedido do depositante: separar o rol civil da ordem de retirada. Campo de lembranças abrangidas: arrancado. Anexo do núcleo obrigatório.')),
 'lacre_lore':('Caderno da conservadora','lacre_lore_found',
   ('Lídia trouxe três pratos ao posto, mas pediu que o nome da filha não seguisse no rol militar.',
    'Deixou o pingente com Inês. No arquivo, guardou apenas a fita correspondente e o recibo de devolução nunca preenchido.',
    'A custódia protegia nomes. Não podia garantir que alguém voltasse para recebê-los.')),
 'lacre_first':('Autorização do primeiro lacre','lacre_first_found',
   ('Original, terceira vigília: R-17 solicita voluntariamente o isolamento das lembranças relativas ao rol encaminhado de Namar.',
    'A impressão corresponde à identificação que carrego. O traço da autorização coincide com a segunda via N-04; não é uma requisição da escolta.',
    'Limite declarado: proteger os nomes contra extração. O restante da folha foi retirado. Eu autorizei um lacre. Não sei tudo que ele deveria conter.')),
 'lacre_second':('Folha sobreposta de revisão','lacre_second_found',
   ('Sob o original há outra folha, de quinta vigília. Lacre suplementar: impedir associação entre depositante, destino e testemunhos.',
    'A primeira impressão foi copiada por decalque. Onde deveria haver nova autorização, há somente um selo de revisão e um espaço vazio.',
    'A anotação corta a borda da folha anterior: a segunda restrição foi aplicada depois. Isso prova uma intervenção distinta, não quem a fez nem se fui ouvido.',
    'Envio para cotejo: Mesa de Revisão do Mosteiro da Vigília. A matriz do selo e a via integral ficaram lá.')),
}
ITEM_FLAGS={key:value[1] for key,value in DOCUMENTS.items()}
ITEM_FLAGS['lacre_lead']='lacre_lead_found'
PUZZLES={
 'vestibule':(('v_bowl','v_lamp','v_name'),'lacre_vestibule_step1','lacre_vestibule_step2','lacre_vestibule_open',('lacre_vestige_seen',)),
 'gallery':(('g_door','g_hand','g_seal'),'lacre_gallery_step1','lacre_gallery_step2','lacre_gallery_open',('lacre_gallery_door_seen','lacre_gallery_hand_seen','lacre_gallery_seal_seen')),
}
