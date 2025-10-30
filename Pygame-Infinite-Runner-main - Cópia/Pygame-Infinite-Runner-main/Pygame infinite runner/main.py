# main.py
import threading
import sys
import os
import time

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from visao import iniciar_thread_visao, deve_saltar, obter_direcao_horizontal
from jogo import ativar_controlo_visao, iniciar_jogo

def main():
    print("=" * 60)
    print("INFINITE RUNNER - CONTROLO POR VISÃO COMPUTACIONAL")
    print("FASE 1: Segmentação por Cor")
    print("=" * 60)
    print("\nInstruções:")
    print("- Mova a mão para ESQUERDA/CENTRO/DIREITA para controlar movimento")
    print("- Levante a mão acima da linha azul para fazer o jogador saltar")
    print("- A segmentação é feita pela cor da pele (espaço YCrCb)")
    print("- Pressione ESC nas janelas de visão para sair")
    print("- Pressione ESPAÇO no jogo para começar/recomeçar")
    print("\nIniciando câmara...")
    
    # Inicia a thread de visão computacional
    iniciar_thread_visao()
    
    # Aguarda a câmara inicializar
    print("Aguardando inicialização da câmara (3 segundos)...")
    time.sleep(3)
    
    # Ativa o controlo por visão no jogo (com salto E movimento lateral)
    ativar_controlo_visao(deve_saltar, obter_direcao_horizontal)
    
    print("Sistema iniciado! As janelas devem estar abertas.")
    print("=" * 60)
    print("\nIniciando o jogo...")
    print("\nControlos:")
    print("  - Mão à ESQUERDA: personagem move-se para a esquerda")
    print("  - Mão ao CENTRO: personagem para")
    print("  - Mão à DIREITA: personagem move-se para a direita")
    print("  - Mão ACIMA da linha azul: personagem salta")
    print("=" * 60)
    
    # Inicia o jogo (bloqueante - roda no main thread)
    iniciar_jogo()

if __name__ == "__main__":
    main()
