# Biblioteca: favoritos accesibles — 2026-10-09

Los botones de estrella de Favoritos, Recientes y resultados solo mostraban símbolos con title. Ahora ofrecen aria-label con la acción y aria-pressed con el estado. En Favoritos se aclara también el title a Quitar favorito. Sin cambios de diseño, almacenamiento ni handlers.

Build Vite aprobado. Playwright MCP en Biblioteca QA, backend 8024 y datos aislados: foco en Marcar favorito, Enter activa favorito/aria-pressed=true; recarga conserva favorito; Quitar favorito lo elimina/aria-pressed=false. Sin modelos ni audio. No certificación con lector de pantalla ni cierre integral de S06-01.

S06-01 continúa parcial, global90,5%. Evidencia complementa contraste exploratorio, navegación, diálogos, ayuda y estados de componentes ya registrados. Próximos gates reales siguen separados del lote ligero: disponibilidad instalada/modos, handoffs/cancelación con pesos y corrección/audio final. Protocolo del piloto permanece sin participantes; no inventar aceptación. Sin commit/push; QA cerrado al terminar.
