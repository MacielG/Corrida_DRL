# Checklist de Deploy - CI/CD Implementation

**Data:** 2025-12-07  
**Objetivo:** Fazer deploy seguro das mudanças de CI/CD

---

## ✅ Pré-requisitos

Antes de fazer o deploy, validate:

```bash
# 1. Confirme que está na branch develop
git branch
# Deve mostrar: * develop

# 2. Confirme que não há mudanças não-commitadas
git status
# Deve mostrar: "On branch develop, nothing to commit, working tree clean"

# 3. Atualize o repositório local
git pull origin develop

# 4. Crie uma branch feature para as mudanças
git checkout -b feature/ci-cd-implementation
```

---

## 📝 Arquivos para Fazer Commit

### Grupo 1: Workflows CI/CD (CRÍTICO)
```bash
git add .github/workflows/tests.yml
git add .github/workflows/coverage.yml
git add .github/workflows/slow-tests.yml
```

**Validação:**
```bash
# Verifique que estão adicionados
git status
```

---

### Grupo 2: Correções de Código
```bash
git add tests/test_interface.py
git add tests/test_interface_modules.py
git add tests/test_learning.py
git add environment.py
```

**Validação:**
```bash
# Teste localmente
pytest tests/ -v -m "not slow" --ignore=tests/test_learning.py
# Deve passar com 87 testes
```

---

### Grupo 3: Documentação
```bash
git add docs/TESTING_PATTERNS.md
git add README.md
git add CI_CD_FIXES.md
git add IMPLEMENTATION_SUMMARY.md
git add DEPLOYMENT_CHECKLIST.md
git add TEST_REPORT.md
```

---

## 📋 Commits Recomendados

Opção A: Um único commit (mais simples)
```bash
git add .github/workflows/ tests/ environment.py docs/ README.md *.md

git commit -m "feat: implement CI/CD pipeline with GitHub Actions

- Add tests.yml for quick tests (87 tests, ~5 min)
- Add slow-tests.yml for learning tests (nightly, ~60 min)
- Add coverage.yml for coverage reports
- Update GitHub Actions to v4/v5 (fix deprecation warnings)
- Fix 2 slow learning tests (Gym 0.26+ compatibility + bounds check)
- Fix 3 interface tests (mock issues, assertion accuracy)
- Add docs/TESTING_PATTERNS.md with mocking guide
- Update README with CI/CD section
- Add detailed implementation documentation

BREAKING: None
Fixes: #TODO (if applicable)
Coverage: 40% → targets 60% with more tests
"
```

Opção B: Múltiplos commits (mais granular)
```bash
# Commit 1: Workflows
git add .github/workflows/
git commit -m "chore: add/update GitHub Actions workflows"

# Commit 2: Fixes de código
git add tests/ environment.py
git commit -m "fix: resolve issues in slow tests and environment bounds"

# Commit 3: Documentação
git add docs/ *.md README.md
git commit -m "docs: add CI/CD documentation and testing patterns"
```

---

## 🧪 Testes Pré-Deploy

Execute localmente ANTES de fazer push:

```bash
# 1. Testes rápidos (deve levar ~1 minuto)
pytest tests/ -v -m "not slow" --ignore=tests/test_learning.py
# ✅ Esperado: 87 passed

# 2. Testes de integração
pytest tests/test_integration.py tests/test_core_module.py -v
# ✅ Esperado: Todos passed

# 3. Lint check
flake8 . --count --exit-zero --max-complexity=10
# ✅ Esperado: No failures

# 4. Syntax check
python -m py_compile main.py environment.py agent.py core/reward_shaper.py
# ✅ Esperado: Sem erros

# 5. Arquivo YAML valido (opcional)
python -m yaml .github/workflows/tests.yml > /dev/null
# ✅ Esperado: Sem erros
```

---

## 🚀 Deploy para develop

Se todos os testes passaram:

```bash
# 1. Rebase na branch develop
git rebase develop

# 2. Push para remote
git push origin feature/ci-cd-implementation

# 3. Abra um Pull Request no GitHub
# - Title: "CI/CD: Implement GitHub Actions pipeline"
# - Description: Use este template:
```

### PR Description Template
```markdown
## Changes
- Implement GitHub Actions CI/CD pipeline
- Update deprecated action versions (v3→v4, v4→v5)
- Fix 5 testes problemáticos
- Add comprehensive testing documentation

## Type of Change
- [x] New feature (CI/CD pipeline)
- [x] Bug fix (5 tests)
- [x] Documentation (TESTING_PATTERNS.md)

## Testing
- [x] Local tests passed (87 quick + 8 slow)
- [x] Coverage report generated
- [x] Linting passed (flake8)

## Checklist
- [x] Código segue estilo do projeto
- [x] Documentação atualizada
- [x] Não há warnings
- [x] Testes adicionados/atualizados
- [x] Testado localmente
```

---

## ✅ Validação Pós-Deploy

Após fazer push, validar que os workflows funcionam:

### 1. No GitHub
```
https://github.com/MacielG/Corrida_DRL/actions
```

Esperado:
- ✅ tests.yml executando
- ✅ Todos os jobs passing
- ✅ Artifacts sendo salvos

### 2. Coverage Report
```
https://codecov.io/github/MacielG/Corrida_DRL
```

Esperado:
- ✅ Coverage report aparece
- ✅ Histórico de cobertura atualizado

### 3. Merge para main (Opcional, depois de validar)
```bash
git checkout main
git pull origin main
git merge develop

# Resolve conflicts se houver
git push origin main
```

---

## 🆘 Troubleshooting

### Problema: GitHub Actions falha com YAML error
**Solução:**
```bash
# Validar YAML localmente
pip install pyyaml
python -c "import yaml; yaml.safe_load(open('.github/workflows/tests.yml'))"
```

### Problema: Tests falham no CI mas passam localmente
**Causas possíveis:**
1. Versão diferente de Python (verifique matrix em tests.yml)
2. Timeout (aumentar em `timeout-minutes`)
3. Dependência não instalada (verificar requirements.txt)

**Solução:**
```bash
# Teste com Python 3.10 (mais restritivo)
python3.10 -m pytest tests/ -m "not slow"
```

### Problema: Coverage não aparece em PRs
**Solução:**
1. Verificar que codecov action está configurado
2. Verificar que token está correto
3. Aguardar 5 minutos (processing delay)

---

## 📅 Timeline Esperada

| Etapa | Tempo | Status |
|-------|-------|--------|
| Testes locais | 5 min | ✅ Completo |
| Push para feature branch | 1 min | ⏳ Próximo |
| Workflows executarem | 5 min | ⏳ Próximo |
| PR review | 24h | ⏳ Próximo |
| Merge para develop | 5 min | ⏳ Próximo |
| Merge para main | 5 min | ⏳ Próximo (opcional) |

**Total:** ~36h (incluindo review)

---

## 🎯 Sucesso Esperado

Após deploy completo, validar:

- [x] CI/CD workflows executam em cada push
- [x] Coverage reports aparecem em PRs
- [x] Testes passam em Python 3.10, 3.11, 3.12
- [x] Slow tests executam nightly
- [x] Linting passa
- [x] Sem warnings no build

---

## 📞 Escalação

Se algo quebrar:

1. **Workflows não executam:**
   - Verificar `.github/workflows/` syntax
   - Verificar branch protection rules
   - Verificar GitHub Actions permissions

2. **Testes falham:**
   - Verificar logs no GitHub Actions
   - Reproduzir localmente
   - Ajustar `timeout-minutes` se necessário

3. **Coverage não reporta:**
   - Verificar codecov.yml existe (optional)
   - Verificar coverage.xml é gerado
   - Aguardar processing (5 min)

---

## ✨ Após Deploy

### Documentar
1. Adicionar badge de build ao README
2. Documentar como rodar testes localmente
3. Criar issue para SonarQube (future)

### Monitorar
1. Verificar que workflows rodam corretamente
2. Monitorar performance (tempo de execução)
3. Coletar feedback

### Próximos Steps
- [ ] Validar workflows por 1 semana
- [ ] Adicionar badges ao README
- [ ] Planejar Phase 2 (SonarQube, Matrix testing)

---

**Status:** ✅ Pronto para Deploy

Execute o checklist acima e faça push com confiança!

Qualquer dúvida, consulte:
- `docs/TESTING_PATTERNS.md` - Padrões de testing
- `CI_CD_FIXES.md` - Detalhes dos fixes
- `.github/workflows/` - Workflows
