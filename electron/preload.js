const { contextBridge, ipcRenderer } = require('electron');

// يمكن استخدام هذا الملف لربط واجهة المستخدم بوظائف النظام بأمان
// حالياً، التطبيق يعمل كـ Web App خالص، لذا لا نحتاج لكثير من التعديلات هنا
contextBridge.exposeInMainWorld('electron', {
  // يمكن إضافة وظائف مستقبلية هنا مثل الطباعة أو حفظ الملفات محلياً
});