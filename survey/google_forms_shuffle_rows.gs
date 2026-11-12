/**
 * C, D1, D2, D3 ızgaralarında "Satır sırasını karıştır" ayarını açar.
 *
 * FormApp'te ızgaralar için karıştırma yöntemi yoktur; ayar Google Forms REST API'deki
 * Grid.shuffleQuestions alanıyla yapılır (forms.batchUpdate).
 *
 * Kullanım: bu dosyayı aynı Apps Script projesine yeni bir dosya olarak ekleyin, üstteki
 * fonksiyon listesinden shuffleGridRows'u seçip Çalıştır'a basın. İlk çalıştırmada Drive ve
 * harici istek izinleri istenir. Form, buildForm()'un verdiği başlıkla Drive'da aranır;
 * aynı başlıkta birden fazla form varsa en son değiştirilen kullanılır. Belirli bir formu
 * hedeflemek için FORM_ID'ye düzenleme bağlantısındaki kimliği yazın (/forms/d/<KİMLİK>/edit).
 */
const FORM_ID = '1MOAOnv2NTTc06z-WehpvQjfrMoMvraAUneYPXmWMZ7Q';
const FORM_TITLE = 'Yeşil Hidrojen Üretim Tesisi Yer Seçimi — Uzman Değerlendirmesi';
const GRID_PREFIXES = ['C.', 'D1.', 'D2.', 'D3.'];

function shuffleGridRows() {
  const formId = FORM_ID || findFormId_();
  Logger.log('Form: ' + DriveApp.getFileById(formId).getName() + ' (' + formId + ')');

  const base = 'https://forms.googleapis.com/v1/forms/' + formId;
  const headers = {Authorization: 'Bearer ' + ScriptApp.getOAuthToken()};
  const form = JSON.parse(UrlFetchApp.fetch(base, {headers: headers}).getContentText());

  const requests = [];
  (form.items || []).forEach(function (it, idx) {
    const title = (it.title || '').trim();
    const isTarget = GRID_PREFIXES.some(function (p) { return title.indexOf(p) === 0; });
    if (!isTarget || !it.questionGroupItem || !it.questionGroupItem.grid) return;
    const qgi = JSON.parse(JSON.stringify(it.questionGroupItem));
    qgi.grid.shuffleQuestions = true;
    requests.push({updateItem: {
      item: {itemId: it.itemId, title: it.title, questionGroupItem: qgi},
      location: {index: idx},
      updateMask: 'questionGroupItem.grid.shuffleQuestions'
    }});
    Logger.log('Karıştırma açılacak: ' + title);
  });
  if (requests.length !== GRID_PREFIXES.length) {
    throw new Error(GRID_PREFIXES.length + ' ızgara bekleniyordu, ' + requests.length + ' bulundu. Başlıkları kontrol edin.');
  }

  const resp = UrlFetchApp.fetch(base + ':batchUpdate', {
    method: 'post', contentType: 'application/json', headers: headers,
    payload: JSON.stringify({requests: requests}), muteHttpExceptions: true
  });
  if (resp.getResponseCode() !== 200) throw new Error('Forms API hatası: ' + resp.getContentText());

  // Doğrulama: ayarı yeniden oku
  const check = JSON.parse(UrlFetchApp.fetch(base, {headers: headers}).getContentText());
  check.items.forEach(function (it) {
    if (it.questionGroupItem && it.questionGroupItem.grid) {
      Logger.log((it.title || '').substring(0, 45) + ' → shuffle = ' + !!it.questionGroupItem.grid.shuffleQuestions);
    }
  });
}

function findFormId_() {
  const files = DriveApp.searchFiles('mimeType = "' + MimeType.GOOGLE_FORMS + '" and title = "' +
                                     FORM_TITLE.replace(/"/g, '\\"') + '" and trashed = false');
  let best = null;
  while (files.hasNext()) {
    const f = files.next();
    if (!best || f.getLastUpdated() > best.getLastUpdated()) best = f;
  }
  if (!best) throw new Error('Form bulunamadı; FORM_ID değerini elle girin.');
  return best.getId();
}
