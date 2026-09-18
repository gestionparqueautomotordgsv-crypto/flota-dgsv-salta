if prox>0 and km>=prox: return "SERVI" # ya pasó -> azul
if prox>0 and km>=prox-1000: return "ALERTA" # falta 1000km -> va en NORMAL pero con alerta amarilla
