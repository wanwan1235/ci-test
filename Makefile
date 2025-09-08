.PHONY: llm-patch apply-patch revert last

# 使い方: make llm-patch ISSUE=1
llm-patch:
	@[ -n "$(ISSUE)" ] || (echo "ISSUE=<number> を指定してください"; exit 1)
	mkdir -p patches
	python3 scripts/llm.py $(ISSUE) > patches/issue-$(ISSUE).patch
	@echo "---- Generated patch: patches/issue-$(ISSUE).patch ----"

# 使い方: make apply-patch ISSUE=1
apply-patch:
	@[ -n "$(ISSUE)" ] || (echo "ISSUE=<number> を指定してください"; exit 1)
	git apply --index patches/issue-$(ISSUE).patch
	git status --porcelain

# 直前のパッチを巻き戻す（適用直後に使う）
revert:
	@git apply -R --index patches/issue-$(ISSUE).patch || echo "revert 失敗（ISSUEを確認）"

# 直近生成のパッチ名を見る
last:
	@ls -1t patches/issue-*.patch | head -n1
