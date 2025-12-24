const { app, BrowserWindow, shell, Menu } = require('electron');
const path = require('path');

// إيقاف التسريع المادي إذا لزم الأمر لحل مشاكل العرض في بعض الأجهزة
// app.disableHardwareAcceleration();

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    icon: path.join(__dirname, '../icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      devTools: false // تغيير إلى true إذا كنت تريد أدوات المطور
    }
  });

  // تحميل ملفات التطبيق المبنية (نفس الملفات التي يستخدمها الموبايل)
  mainWindow.loadFile(path.join(__dirname, '../www/index.html'));

  // إخفاء القائمة العلوية الافتراضية للحصول على مظهر تطبيق أنظف
  mainWindow.setMenuBarVisibility(false);

  // التعامل مع الروابط الخارجية (مثل البوابة التعليمية ومنصة نور)
  // هذا يضمن فتح الروابط في المتصفح الافتراضي للكمبيوتر (Chrome/Edge) بدلاً من نافذة داخل التطبيق
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});