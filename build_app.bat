@echo off
REM Di chuyển vào thư mục chứa app.py
cd /d E:\TAI_LIEU\AI\new_app

REM Xóa build cũ (tùy chọn, để tránh rác)
rmdir /s /q build
rmdir /s /q dist
del app.spec

REM Build lại app.exe bằng PyInstaller
python -m PyInstaller --noconsole --onefile app.py

REM Copy file exe ra thư mục chính
copy dist\app.exe app.exe

echo ============================================
echo Build hoàn tất! File app.exe đã sẵn sàng.
echo Bạn có thể chạy trực tiếp bằng app.exe
echo ============================================
pause
