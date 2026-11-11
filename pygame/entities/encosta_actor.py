"""A registrar who stays for missing people and an escort who distrusts authorizations."""
from entities.npc import NPC


class EncostaNPC(NPC):
    def __init__(self,uid,name,position,load):
        super().__init__(uid,name,position,{'default':()},
            load(f'assets/vale_characters/{uid}_idle.png'),
            run_sprite=load(f'assets/vale_characters/{uid}_walk.png'),frame_size=32,draw_size=64)
        self.story=None

    def dialogue_for(self,state,manager=None):
        s=self.story
        if self.uid=='ines' and s and s.get('lacre_return_seen'):
            return self.dialogues['default']
        if self.uid=='ines':
            if s and s.get('encosta_choice_shared'):
                return ('Minha assinatura está aí, sim. Entreguei nomes à Câmara. Não entreguei pessoas à escolta.',
                        'Sei o que parece. Também sei o que acontecia quando qualquer cor requisitava um nome.',
                        'Lídia levou o rol. Eu fiquei para devolver objetos a quem voltasse. Ainda não devolvi o dela.',
                        'Obrigada por me deixar ler a acusação. Compare a planta, perto do armário. Não precisa acreditar só em mim.')
            if s and s.get('encosta_choice_kept'):
                return ('Vai guardar a folha? Então guarde inteira. Até a margem que me acusa.',
                        'Eu assinei a custódia dos nomes. O comentário não é meu. Não sei quem escreveu.',
                        'A planta fica perto do armário. Se encontrar Lídia, pergunte a ela por que levou o rol.',
                        'Quando tiver uma resposta, não deixe meu nome virar só uma suspeita conveniente.')
            if s and s.get('ines_met'):
                return ('Ainda deixo o terceiro prato. É hábito, não sinal de que sei quando ela volta.',
                        'O livro conta quem recebeu comida. O armário guarda o que não podíamos entregar a um uniforme.',
                        'Se a pedra lhe disser alguma coisa, ouça o que falta junto do que ouviu.')
            return ('Sou Inês. Não remexa nos pratos: estão lavados. Gosto de deixar o lugar pronto.',
                    'Você trouxe um recibo do Vale? Eu registrava recebimentos aqui. Não decidia o destino de quem vinha.',
                    'O posto esvaziou em grupos. Uns saíram para a estrada. Outros, para a Câmara. O livro não distingue todos.',
                    'Fiquei pelos objetos que ainda têm dono. E por Lídia. Não encontrei uma baixa que me permita parar de esperar.')
        consequence=('Mara escreveu que alguém segurou a carroça. Sua placa estava na descrição. Isso me dá uma coisa concreta para pesar.'
                     if s and s.get('namar_choice_protect') else
                     'Mara escreveu sobre a carga perdida e o homem que correu atrás do índice. Se trouxe papéis, mostre o que eles fizeram por alguém.')
        if s and s.get('breno_met'):
            return (('Inês pôde responder à folha. Melhor assim.' if s.get('encosta_choice_shared') else
                     'Guardar um papel não faz dele uma resposta. Também não faz de Inês culpada.'),
                    'Eu escoltava remessas. A placa R-17 autorizava a passagem, mas o selo de custódia mantinha o rol separado.',
                    'Já vi as duas cores pedirem os mesmos nomes. Nunca vi nenhuma explicar para quê.')
        return ('Breno. Pare onde está. Essa peça no cinto é uma autorização de escolta vermelha.',
                'Não disse que conheço você. Conheço o que alguém podia mandar usando essa marca.',
                consequence,
                'A Câmara recebia os nomes fora dos livros militares. Isso pode ter protegido gente. Pode ter escondido gente também.',
                'Olhe o registro e o selo. Depois escute o posto antes de subir o arco norte.')
