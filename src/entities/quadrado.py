#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo da classe Quadrado, que representa tanto o jogador quanto os inimigos.
"""

import pygame
import math
import random
from src.config import *
from src.entities.tiro import Tiro
from src.utils.sound import gerar_som_tiro
import os
import json

class Quadrado:
    """
    Classe para os quadrados (jogador e inimigo).
    Contém toda a lógica de movimento, tiros e colisões.
    """
    def __init__(self, x, y, tamanho, cor, velocidade):
        self.x = x
        self.y = y
        self.tamanho = tamanho
        self.cor = cor
        self.cor_escura = self._gerar_cor_escura(cor)
        self.cor_brilhante = self._gerar_cor_brilhante(cor)
        self.velocidade = velocidade
        
        # Verificar se é o jogador e carregar upgrade de vida
        if cor == AZUL:  # Se for o jogador
            vidas_upgrade = self._carregar_upgrade_vida()
            self.vidas = vidas_upgrade
            self.vidas_max = vidas_upgrade
        else:  # Se for inimigo
            self.vidas = 1  # Padrão: 1 vida para inimigos normais
            self.vidas_max = 1
        
        self.rect = pygame.Rect(x, y, tamanho, tamanho)
        self.tempo_ultimo_tiro = 0
        
        # Cooldown variável para inimigos
        if cor == AZUL:  # Azul = jogador
            self.tempo_cooldown = COOLDOWN_TIRO_JOGADOR
        else:
            # Para inimigos, o cooldown é baseado no quão "vermelho" é o inimigo
            vermelhidao = cor[0] / 255.0
            self.tempo_cooldown = COOLDOWN_TIRO_INIMIGO + int(vermelhidao * 200)  # 400-600ms
        
        self.invulneravel = False
        self.tempo_invulneravel = 0
        self.duracao_invulneravel = DURACAO_INVULNERAVEL
        
        # Trilha de movimento
        self.posicoes_anteriores = []
        self.max_posicoes = 15
        
        # Estética adicional
        self.angulo = 0
        self.pulsando = 0
        self.tempo_pulsacao = 0
        
        # Efeito de dano
        self.efeito_dano = 0
        
        # Identificador (útil para fases)
        self.id = id(self)
    def _carregar_upgrade_vida(self):
        """
        Carrega o upgrade de vida do arquivo de upgrades.
        Retorna 1 se não houver upgrade.
        """
        try:
            # Verificar se o arquivo existe
            if os.path.exists("data/upgrades.json"):
                with open("data/upgrades.json", "r") as f:
                    upgrades = json.load(f)
                    return upgrades.get("vida", 1)
            return 1
        except Exception as e:
            print(f"Erro ao carregar upgrade de vida: {e}")
            return 1
        
    
    def _gerar_cor_escura(self, cor):
        """Gera uma versão mais escura da cor."""
        return tuple(max(0, c - 50) for c in cor)
    
    def _gerar_cor_brilhante(self, cor):
        """Gera uma versão mais brilhante da cor."""
        return tuple(min(255, c + 70) for c in cor)

    def desenhar(self, tela):
        """Desenha o quadrado na tela com seus efeitos visuais."""
        # Desenhar trilha de movimento para o inimigo (qualquer coisa diferente de AZUL)
        if self.cor != AZUL:
            for i, (pos_x, pos_y) in enumerate(self.posicoes_anteriores):
                alpha = int(255 * (1 - i / len(self.posicoes_anteriores)))
                # Garantir que os valores RGB estejam no intervalo válido (0-255)
                cor_trilha = (max(0, min(255, self.cor[0] - 100)), 
                              max(0, min(255, self.cor[1] - 100)), 
                              max(0, min(255, self.cor[2] - 100)))
                tamanho = int(self.tamanho * (1 - i / len(self.posicoes_anteriores) * 0.7))
                pygame.draw.rect(tela, cor_trilha, 
                                (pos_x + (self.tamanho - tamanho) // 2, 
                                 pos_y + (self.tamanho - tamanho) // 2, 
                                 tamanho, tamanho))
        
        # Se estiver invulnerável, pisca o quadrado
        if self.invulneravel and pygame.time.get_ticks() % 200 < 100:
            return
        
        # Efeito de pulsação
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_pulsacao > 100:
            self.tempo_pulsacao = tempo_atual
            self.pulsando = (self.pulsando + 1) % 12
            
        mod_tamanho = 0
        if self.pulsando < 6:
            mod_tamanho = self.pulsando
        else:
            mod_tamanho = 12 - self.pulsando
            
        # Desenhar sombra
        pygame.draw.rect(tela, (20, 20, 20), 
                        (self.x + 4, self.y + 4, 
                         self.tamanho, self.tamanho), 0, 3)
        
        # Desenhar o quadrado com bordas arredondadas
        cor_uso = self.cor
        if self.efeito_dano > 0:
            cor_uso = BRANCO
            self.efeito_dano -= 1
        
        # Quadrado interior
        pygame.draw.rect(tela, self.cor_escura, 
                        (self.x, self.y, 
                         self.tamanho + mod_tamanho, self.tamanho + mod_tamanho), 0, 5)
        
        # Quadrado exterior (menor)
        pygame.draw.rect(tela, cor_uso, 
                        (self.x + 3, self.y + 3, 
                         self.tamanho + mod_tamanho - 6, self.tamanho + mod_tamanho - 6), 0, 3)
        
        # Brilho no canto superior esquerdo
        pygame.draw.rect(tela, self.cor_brilhante, 
                        (self.x + 5, self.y + 5, 
                         8, 8), 0, 2)
        
        # Desenhar indicador de vidas (barra de vida)
        vida_largura = 50
        altura_barra = 6
        
        # Fundo escuro
        pygame.draw.rect(tela, (40, 40, 40), 
                        (self.x, self.y - 15, vida_largura, altura_barra), 0, 2)
        
        # Vida atual
        vida_atual = int((self.vidas / self.vidas_max) * vida_largura)
        if vida_atual > 0:
            pygame.draw.rect(tela, self.cor, 
                            (self.x, self.y - 15, vida_atual, altura_barra), 0, 2)


    def mover(self, dx, dy):
        """Move o quadrado na direção especificada, com lógica melhorada para evitar tremores."""
        # Salvar posição atual para a trilha (apenas inimigos)
        if self.cor != AZUL:
            self.posicoes_anteriores.insert(0, (self.x, self.y))
            if len(self.posicoes_anteriores) > self.max_posicoes:
                self.posicoes_anteriores.pop()
        
        # Calcular nova posição
        novo_x = self.x + dx * self.velocidade
        novo_y = self.y + dy * self.velocidade
        
        # Flag para indicar comportamento de fuga da borda
        em_fuga_da_borda = False
        
        # Verificar comportamento de inimigos perto das bordas
        if self.cor != AZUL:  # Somente para inimigos
            # Margens para detecção de proximidade com bordas
            margem_seguranca = 50
            margem_critica = 20
            
            # Verificar se está em zona crítica (muito perto da borda)
            em_zona_critica = (novo_x < margem_critica or 
                            novo_x > LARGURA - self.tamanho - margem_critica or
                            novo_y < margem_critica or 
                            novo_y > ALTURA - self.tamanho - margem_critica)
            
            # Verificar se está em zona de segurança (perto da borda, mas não crítico)
            em_zona_seguranca = (novo_x < margem_seguranca or 
                            novo_x > LARGURA - self.tamanho - margem_seguranca or
                            novo_y < margem_seguranca or 
                            novo_y > ALTURA - self.tamanho - margem_seguranca)
            
            if em_zona_critica:
                # Se está muito perto da borda, aplicar um impulso forte para o centro
                em_fuga_da_borda = True
                
                # Determinar direção para o centro
                centro_x = LARGURA / 2
                centro_y = ALTURA / 2
                
                # Calcular vetor para o centro
                vetor_x = centro_x - self.x
                vetor_y = centro_y - self.y
                
                # Normalizar vetor
                distancia = math.sqrt(vetor_x**2 + vetor_y**2)
                if distancia > 0:
                    vetor_x /= distancia
                    vetor_y /= distancia
                
                # Aplicar movimento em direção ao centro com impulso forte
                impulso = 1.5  # Mais forte para escapar rapidamente
                novo_x = self.x + vetor_x * self.velocidade * impulso
                novo_y = self.y + vetor_y * self.velocidade * impulso
                
            elif em_zona_seguranca:
                # Se está na zona de segurança mas não crítica, suavizar movimento
                # Combinamos o movimento original com um vetor para o centro
                centro_x = LARGURA / 2
                centro_y = ALTURA / 2
                
                # Calcular vetor para o centro
                vetor_x = centro_x - self.x
                vetor_y = centro_y - self.y
                
                # Normalizar vetor
                distancia = math.sqrt(vetor_x**2 + vetor_y**2)
                if distancia > 0:
                    vetor_x /= distancia
                    vetor_y /= distancia
                
                # Misturar o movimento original com movimento para o centro
                fator_mistura = 0.6  # 60% direção centro, 40% movimento original
                novo_x = self.x + ((vetor_x * fator_mistura) + (dx * (1 - fator_mistura))) * self.velocidade
                novo_y = self.y + ((vetor_y * fator_mistura) + (dy * (1 - fator_mistura))) * self.velocidade
        
        # Verificar limites da tela e ajustar posição
        if 0 <= novo_x <= LARGURA - self.tamanho:
            self.x = novo_x
        else:
            # Se for inimigo em fuga da borda, aplicar um impulso forte para dentro
            if self.cor != AZUL:
                if novo_x < 0:
                    self.x = 10  # Impulso forte para dentro
                else:
                    self.x = LARGURA - self.tamanho - 10
            else:
                # O jogador simplesmente fica na borda
                self.x = max(0, min(novo_x, LARGURA - self.tamanho))
        
        if 0 <= novo_y <= ALTURA - self.tamanho:
            self.y = novo_y
        else:
            # Se for inimigo em fuga da borda, aplicar um impulso forte para dentro
            if self.cor != AZUL:
                if novo_y < 0:
                    self.y = 10
                else:
                    self.y = ALTURA - self.tamanho - 10
            else:
                # O jogador simplesmente fica na borda
                self.y = max(0, min(novo_y, ALTURA - self.tamanho))
        
        # Atualizar o retângulo de colisão
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Atualizar ângulo para efeito visual
        if dx != 0 or dy != 0:
            self.angulo = (self.angulo + 5) % 360

    def atirar(self, tiros, direcao=None):
        """Faz o quadrado atirar na direção especificada."""
        # Verificar cooldown
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_tiro < self.tempo_cooldown:
            return
        
        self.tempo_ultimo_tiro = tempo_atual
        
        # Posição central do quadrado
        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2
        
        # Som de tiro
        pygame.mixer.Channel(1).play(pygame.mixer.Sound(gerar_som_tiro()))
        
        # Se não foi especificada uma direção, atira em linha reta
        if direcao is None:
            # Jogador atira para a direita
            if self.cor == AZUL:
                tiros.append(Tiro(centro_x, centro_y, 1, 0, AMARELO, 8))
            # Inimigo atira para a esquerda
            else:
                # Cor do tiro varia com a cor do inimigo
                cor_tiro = VERDE
                # Misturar um pouco da cor do inimigo no tiro
                if self.cor != VERMELHO:
                    verde_base = VERDE[1]
                    r = min(255, self.cor[0] // 3)  # Um pouco da componente vermelha
                    g = verde_base  # Manter o verde forte
                    b = min(255, self.cor[2] // 2)  # Um pouco da componente azul
                    cor_tiro = (r, g, b)
                    
                tiros.append(Tiro(centro_x, centro_y, -1, 0, cor_tiro, 7))
        else:
            # Cor do tiro baseada no tipo de quadrado
            cor_tiro = AMARELO if self.cor == AZUL else VERDE
            if self.cor != AZUL and self.cor != VERMELHO:
                # Misturar cores para inimigos especiais
                verde_base = VERDE[1]
                r = min(255, self.cor[0] // 3)
                g = verde_base
                b = min(255, self.cor[2] // 2)
                cor_tiro = (r, g, b)
                
            tiros.append(Tiro(centro_x, centro_y, direcao[0], direcao[1], cor_tiro, 7))

    def tomar_dano(self):
        """
        Faz o quadrado tomar dano.
        Retorna True se o dano foi aplicado, False se estava invulnerável.
        """
        if not self.invulneravel:
            self.vidas -= 1
            self.invulneravel = True
            self.tempo_invulneravel = pygame.time.get_ticks()
            self.efeito_dano = 10  # Frames de efeito visual
            return True
        return False

    def atualizar(self):
        """Atualiza o estado do quadrado."""
        # Verificar se o tempo de invulnerabilidade acabou
        if self.invulneravel and pygame.time.get_ticks() - self.tempo_invulneravel > self.duracao_invulneravel:
            self.invulneravel = False