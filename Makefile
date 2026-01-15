.PHONY: validate-metadata generate-ro-crate

validate-metadata:
	python scripts/validate_metadata.py

generate-ro-crate:
	python scripts/generate_ro_crate.py

