.PHONY: bootstrap test app validate package

bootstrap:
	python scripts/bootstrap.py

test:
	python -m pytest

app:
	streamlit run app.py

validate:
	python scripts/validate_project.py

package:
	python scripts/package_submission.py
