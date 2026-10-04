"""Smoke test: uygulamanın hatasız açıldığını doğrular. Çalıştır: python test_app.py"""
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py", default_timeout=90).run()
assert not at.exception, at.exception
# Tüm dönem + ML tahmini
at.selectbox[0].select("Tüm Dönem").run()
assert not at.exception, at.exception
at.button[0].click().run()
assert not at.exception, at.exception
print("OK: hata yok. Uyarı/hata kutuları:", [e.value for e in at.error])
