# visao.py
import cv2
import numpy as np
import threading

_posicao_atual = (None, None)
_camera_ativa = False
_altura_referencia = None
_largura_frame = 640


def iniciar_visao():
    """Inicia a captura da câmara e atualiza continuamente a posição da mão."""
    global _posicao_atual, _camera_ativa, _altura_referencia, _largura_frame
    _camera_ativa = True

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    _largura_frame = 640
    altura_frame = 480
    _altura_referencia = altura_frame // 2  # Linha de referência no meio

    # Variáveis para calibração com clique do rato (opcional)
    # calibrar = False

    # def mouse_callback(event, x, y, flags, param):
    #     """Callback para calibrar a cor da pele com clique do rato."""
    #     nonlocal calibrar
    #     if event == cv2.EVENT_LBUTTONDOWN:
    #         calibrar = True
    #         frame_calibracao = param
    #         # Pegar uma região 5x5 em torno do clique
    #         roi = frame_calibracao[max(0, y - 2):min(480, y + 3), max(0, x - 2):min(640, x + 3)]
    #         if roi.size > 0:
    #             # Calcular valores médios da região
    #             ycrcb_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2YCrCb)
    #             mean_vals = cv2.mean(ycrcb_roi)[:3]
    #             print(f"Cor calibrada em ({x},{y}): Y={mean_vals[0]:.1f}, Cr={mean_vals[1]:.1f}, Cb={mean_vals[2]:.1f}")

    cv2.namedWindow("Camera - Segmentacao por Cor")

    while _camera_ativa:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        frame_original = frame.copy()

        # Callback para calibração (clique na mão para ajustar)
        # cv2.setMouseCallback("Camera - Segmentacao por Cor", mouse_callback, frame)

        # Converter para YCrCb (melhor para detecção de pele)
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)

        # Limites ajustados para evitar vermelhos puros
        lower_skin = np.array([0, 135, 85], dtype=np.uint8)
        upper_skin = np.array([255, 180, 135], dtype=np.uint8)

        # Criar máscara
        mask = cv2.inRange(ycrcb, lower_skin, upper_skin)

        # Filtro adicional no espaço HSV para remover vermelhos
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Remover vermelhos (Hue 0-10 e 170-180)
        lower_red1 = np.array([0, 100, 100], dtype=np.uint8)
        upper_red1 = np.array([10, 255, 255], dtype=np.uint8)
        lower_red2 = np.array([170, 100, 100], dtype=np.uint8)
        upper_red2 = np.array([180, 255, 255], dtype=np.uint8)

        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        # Remover vermelhos da máscara de pele
        mask = cv2.bitwise_and(mask, cv2.bitwise_not(mask_red))

        # Operações morfológicas para remover ruído
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.erode(mask, kernel, iterations=2)
        mask = cv2.dilate(mask, kernel, iterations=2)

        # Fechar pequenos buracos
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Suavizar bordas
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        # Re-binarizar após blur
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

        # Encontrar contornos
        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        frame_visualizacao = frame.copy()

        # Desenhar linha de referência horizontal (para salto)
        cv2.line(frame_visualizacao, (0, _altura_referencia), (_largura_frame, _altura_referencia),
                 (255, 0, 0), 2)
        cv2.putText(frame_visualizacao, "Linha de Salto", (10, _altura_referencia - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        # Desenhar linhas verticais para divisão esquerda/centro/direita
        zona_esquerda = _largura_frame // 3
        zona_direita = 2 * _largura_frame // 3

        cv2.line(frame_visualizacao, (zona_esquerda, 0), (zona_esquerda, altura_frame),
                 (0, 255, 255), 2)
        cv2.line(frame_visualizacao, (zona_direita, 0), (zona_direita, altura_frame),
                 (0, 255, 255), 2)

        # Labels das zonas
        cv2.putText(frame_visualizacao, "ESQUERDA", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame_visualizacao, "CENTRO", (zona_esquerda + 50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame_visualizacao, "DIREITA", (zona_direita + 50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        if contornos:
            # Encontrar o maior contorno (assumindo que é a mão)
            maior = max(contornos, key=cv2.contourArea)

            if cv2.contourArea(maior) > 3000:
                # Calcular o centro de gravidade (centróide) usando momentos
                M = cv2.moments(maior)

                if M["m00"] != 0:
                    # Centro de gravidade
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    _posicao_atual = (cx, cy)

                    # Visualização - APENAS contornos e centro de gravidade
                    # Desenhar o contorno da mão
                    cv2.drawContours(frame_visualizacao, [maior], -1, (0, 255, 0), 2)

                    # Desenhar o centro de gravidade
                    cv2.circle(frame_visualizacao, (cx, cy), 8, (0, 0, 255), -1)
                    cv2.circle(frame_visualizacao, (cx, cy), 10, (255, 255, 255), 2)

                    # Determinar zona horizontal
                    if cx < zona_esquerda:
                        direcao = "ESQUERDA"
                        cor_direcao = (255, 100, 100)
                    elif cx > zona_direita:
                        direcao = "DIREITA"
                        cor_direcao = (100, 100, 255)
                    else:
                        direcao = "CENTRO"
                        cor_direcao = (100, 255, 100)

                    # Mostrar coordenadas do centro de gravidade
                    cv2.putText(frame_visualizacao, f"Pos: ({cx}, {cy})", (cx + 15, cy - 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    # Mostrar direção
                    cv2.putText(frame_visualizacao, direcao, (cx + 15, cy + 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor_direcao, 2)

                    # Mostrar área do contorno
                    #area = cv2.contourArea(maior)
                    #cv2.putText(frame_visualizacao, f"Area: {int(area)}", (cx + 15, cy + 25),
                    #           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

                    # Indicador de salto
                    if cy < _altura_referencia:
                        cv2.putText(frame_visualizacao, "SALTO!", (250, 100),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                        cv2.circle(frame_visualizacao, (cx, cy), 15, (0, 255, 0), 3)

        # Mostrar instruções
        cv2.putText(frame_visualizacao, "Mova a mao: Esquerda/Centro/Direita | Suba: Saltar",
                    (10, altura_frame - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(frame_visualizacao, "ESC: sair", (10, altura_frame - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        # cv2.putText(frame_visualizacao, "ESC: sair | Clique: calibrar cor", (10, altura_frame - 10),
        #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Camera - Segmentacao por Cor", frame_visualizacao)
        cv2.imshow("Mascara - Resultado da Segmentacao", mask)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC para sair
            _camera_ativa = False
            break

    cap.release()
    cv2.destroyAllWindows()


def obter_posicao_atual():
    """Devolve a última posição (x, y) detectada (centro de gravidade)."""
    global _posicao_atual
    return _posicao_atual


def obter_direcao_horizontal():
    """
    Retorna a direção horizontal baseada na posição da mão:
    -1: Esquerda
     0: Centro
     1: Direita
    """
    global _posicao_atual, _largura_frame
    if _posicao_atual[0] is not None:
        cx = _posicao_atual[0]
        zona_esquerda = _largura_frame // 3
        zona_direita = 2 * _largura_frame // 3

        if cx < zona_esquerda:
            return -1  # Esquerda
        elif cx > zona_direita:
            return 1  # Direita
        else:
            return 0  # Centro
    return 0


def deve_saltar():
    """Retorna True se a mão está acima da linha de referência (deve saltar)."""
    global _posicao_atual, _altura_referencia
    if _posicao_atual[1] is not None and _altura_referencia is not None:
        return _posicao_atual[1] < _altura_referencia
    return False


def parar_visao():
    """Para a thread de visão."""
    global _camera_ativa
    _camera_ativa = False


def iniciar_thread_visao():
    """Inicia a thread da visão (para ser chamada no main.py)."""
    thread = threading.Thread(target=iniciar_visao, daemon=True)
    thread.start()