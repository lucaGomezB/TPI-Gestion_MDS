# Project Skills — activia-trace

> Registro canónico de skills disponibles en el proyecto.
> Todo agente lee este archivo antes de implementar para cargar las skills correspondientes.

## Skills por Agente

### Backend Core
| Skill | Ruta | Trigger |
|-------|------|---------|
| `fastapi-templates` | `.agents/skills/fastapi-templates/SKILL.md` | FastAPI projects from scratch |
| `test-driven-development` | `.agents/skills/test-driven-development/SKILL.md` | Before writing implementation code |
| `sdd-apply` | `.agents/skills/sdd-apply/SKILL.md` | Implementing tasks from a change |
| `systematic-debugging` | `.agents/skills/systematic-debugging/SKILL.md` | Debugging bugs, test failures |

### Backend Aux
| Skill | Ruta | Trigger |
|-------|------|---------|
| `sdd-apply` | `.agents/skills/sdd-apply/SKILL.md` | Implementing tasks from a change |
| `test-driven-development` | `.agents/skills/test-driven-development/SKILL.md` | Before writing implementation code |
| `systematic-debugging` | `.agents/skills/systematic-debugging/SKILL.md` | Debugging bugs, test failures |

### Frontend
| Skill | Ruta | Trigger |
|-------|------|---------|
| `sdd-apply` | `.agents/skills/sdd-apply/SKILL.md` | Implementing tasks from a change |
| `test-driven-development` | `.agents/skills/test-driven-development/SKILL.md` | Before writing implementation code |
| `code-review-excellence` | `.agents/skills/code-review-excellence/SKILL.md` | PR review, mentoring |
| `react-dev` | `.agents/skills/react-dev/SKILL.md` | React TypeScript components, hooks |
| `fastapi-python` | `.agents/skills/fastapi-python/SKILL.md` | FastAPI Python patterns |

### Orquestacion (OPSX / SDD)
| Skill | Ruta | Trigger |
|-------|------|---------|
| `sdd-propose` | `.agents/skills/sdd-propose/SKILL.md` | Creating change proposals |
| `sdd-design` | `.agents/skills/sdd-design/SKILL.md` | Technical design documents |
| `sdd-spec` | `.agents/skills/sdd-spec/SKILL.md` | Specification documents |
| `sdd-tasks` | `.agents/skills/sdd-tasks/SKILL.md` | Task checklists |
| `sdd-verify` | `.agents/skills/sdd-verify/SKILL.md` | Verify implementation vs specs |
| `sdd-archive` | `.agents/skills/sdd-archive/SKILL.md` | Archive completed changes |
| `openspec-init` | `.agents/skills/openspec-init/SKILL.md` | Initialize OPSX in project |
| `openspec-onboard` | `.agents/skills/openspec-onboard/SKILL.md` | Guided OPSX walkthrough |
| `sdd-apply` | `.agents/skills/sdd-apply/SKILL.md` | Implementing tasks |

### Additional Project Skills
| Skill | Ruta | Trigger |
|-------|------|---------|
| `fastapi` | `.agents/skills/fastapi/SKILL.md` | FastAPI APIs and Pydantic models |
| `find-skills` | `.agents/skills/find-skills/SKILL.md` | Discovering new skills |
| `dashboard-crud-page` | `.agents/skills/dashboard-crud-page/SKILL.md` | Dashboard CRUD pages |
| `tailwind-design-system` | `.agents/skills/tailwind-design-system/SKILL.md` | Tailwind v4 design systems |
| `help-system-content` | `.agents/skills/help-system-content/SKILL.md` | Help content for components |

## Shared References

| Skill | Ruta | Proposito |
|-------|------|-----------|
| `_shared` | `.agents/skills/_shared/SKILL.md` | Internal shared references for SDD/OPSX skills |

## Como Usar

1. Identificar el agente que ejecutara la tarea
2. Cargar TODAS las skills listadas para ese agente ANTES de escribir codigo
3. Multiples skills pueden cargarse simultaneamente
4. Verificar en `.atl/skill-registry.md` las reglas compactas (Project Standards) si aplica

> Generado: 2026-06-12
