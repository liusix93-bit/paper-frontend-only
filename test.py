import fitz
try:
    doc = fitz.open()
    page = doc.new_page()
    r = fitz.Rect(0, 10, 100, 10)
    print("Rect:", r)
    print("is_empty:", r.is_empty)
    pix = page.get_pixmap(clip=r)
    print("Pixmap:", pix)
    pix.save("temp/test.png")
    print("Saved!")
except Exception as e:
    import traceback
    traceback.print_exc()
