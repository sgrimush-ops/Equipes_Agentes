var SPREADSHEET_ID = '1bGgibeiHfnX35Re7joK68Q6AqSif8uJwomuli_xrWGA';
var MODERATOR_PIN = '0104';
var CONSULTANT_PIN = '2512';

function getSheet(name) {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  return ss.getSheetByName(name) || ss.getSheets()[0];
}

function doGet(e) {
  var idTopico = (e && e.parameter && e.parameter.id) ? e.parameter.id : null;
  var template = HtmlService.createTemplateFromFile('index');
  template.idTopicoUrl = idTopico; 
  return template.evaluate()
    .setTitle('Wiki Baklizi')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function getInitialData(idTopico) {
  try {
    return {
      topics: getTopics(),
      categories: getCategories(),
      responsaveis: getResponsaveis(),
      detail: idTopico ? getTopicData(idTopico) : null,
      serverStatus: "OK"
    };
  } catch (e) {
    return { error: e.toString(), serverStatus: "ERROR" };
  }
}

function getTopics() {
  try {
    var sheet = getSheet('Topicos');
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return [];
    
    // RESTAURAÇÃO: Lendo as 12 colunas originais (A até L)
    var data = sheet.getRange(2, 1, lastRow - 1, 12).getValues();
    
    return data.map(function(row) {
      // Prioridade está na coluna 11 (índice 11)
      var pStr = (row[11] || '').toString().trim();
      var p = parseInt(pStr.split('-')[0]) || ""; // Pega o número se for "1-Urgente" ou "1"
      
      return {
        id: (row[0] || '').toString().trim(),
        categoria: (row[1] || 'Geral').toString().trim(),
        titulo: (row[2] || '').toString().trim(),
        descricao: (row[3] || '').toString().trim(),
        status: (row[4] || '').toString().trim(),
        data: (row[5] || '').toString().trim(),
        prioridade: p, // Mantém vazio se não tiver prioridade
        img: (row[6] || '').toString().trim(),
        reportado: (row[7] || 'N/A').toString().trim(),
        responsavel: (row[8] || 'Pendente').toString().trim()
      };
    });
  } catch(e) {
    return [];
  }
}

function addTopic(titulo, categoria, descricao, imgData, imgName, mimeType, reportado, responsavel) {
  try {
    var sheet = getSheet('Topicos');
    var lastId = sheet.getLastRow() > 1 ? sheet.getRange(sheet.getLastRow(), 1).getValue().toString() : "T000";
    var num = parseInt(lastId.replace("T", "")) || 0;
    var newId = "T" + ("00" + (num + 1)).slice(-3);
    
    var imgUrl = "";
    if (imgData) {
      imgUrl = saveToDrive(imgData, imgName, mimeType, "Demanda_" + newId);
    }
    
    var date = Utilities.formatDate(new Date(), "GMT-3", "dd/MM/yyyy");
    // ESTRUTURA FIXA (12 Colunas): ID(0), Cat(1), Tit(2), Desc(3), Status(4), Data(5), Img(6), Rep(7), Resp(8), Sol(9), ImgSol(10), Prio(11)
    sheet.appendRow([newId, categoria, titulo, descricao, 'Sugerida', date, imgUrl, reportado, responsavel, "", "", ""]);
    SpreadsheetApp.flush();
    return {status: "SUCCESS"};
  } catch(e) {
    return {status: "ERROR", error: e.toString()};
  }
}

function approveTopic(id, prioridade) {
  try {
    var sheet = getSheet('Topicos');
    var data = sheet.getDataRange().getValues();
    for (var i = 1; i < data.length; i++) {
      if (data[i][0].toString().trim() === id) {
        sheet.getRange(i + 1, 5).setValue('Aberta');      // Col E (Status)
        sheet.getRange(i + 1, 12).setValue(prioridade);  // Col L (Prioridade - Coluna 12)
        SpreadsheetApp.flush();
        return {status: "SUCCESS"};
      }
    }
    return {status: "NOT_FOUND"};
  } catch(e) {
    return {status: "ERROR", error: e.toString()};
  }
}

function deleteTopic(id) {
  try {
    var sheet = getSheet('Topicos');
    var data = sheet.getDataRange().getValues();
    for (var i = 1; i < data.length; i++) {
      if (data[i][0].toString().trim() === id) {
        sheet.deleteRow(i + 1);
        SpreadsheetApp.flush();
        return {status: "SUCCESS"};
      }
    }
    return {status: "NOT_FOUND"};
  } catch(e) {
    return {status: "ERROR", error: e.toString()};
  }
}

function getTopicData(idTopico) {
  try {
    var sheet = getSheet('Topicos');
    var data = sheet.getDataRange().getValues();
    var row = data.find(function(r) { return r[0] && r[0].toString().trim() == idTopico; });
    if (!row) return null;
    
    var detalhes = {
      id: row[0].toString().trim(),
      categoria: row[1].toString().trim(),
      titulo: row[2].toString().trim(),
      descricao: row[3].toString().trim(),
      status: row[4].toString().trim(),
      data: row[5].toString().trim(),
      img: row[6].toString().trim(),
      reportado: row[7].toString().trim(),
      responsavel: row[8].toString().trim(),
      solucao: (row[9]||"").toString().trim(),
      prioridade: (row[11]||"").toString().trim()
    };
    
    var sheetInter = getSheet('Interacoes');
    var comentarios = [];
    if (sheetInter) {
      var cData = sheetInter.getDataRange().getValues();
      comentarios = cData.slice(1).filter(function(r) { return r[1] == idTopico; }).map(function(r) {
        return { usuario: r[2], texto: r[3], data: r[4] instanceof Date ? Utilities.formatDate(r[4], "GMT-3", "dd/MM/yyyy HH:mm") : r[4] };
      }).reverse();
    }
    return { detalhes: detalhes, comentarios: comentarios };
  } catch(e) { return null; }
}

function addComment(idTopico, usuario, texto) {
  var sheet = getSheet('Interacoes');
  sheet.appendRow([Utilities.getUuid(), idTopico, usuario, texto, new Date()]);
  return { success: true };
}

function saveToDrive(base64Data, fileName, mimeType, prefix) {
  try {
    var folder = getOrCreateFolder("Wikipedia_Uploads");
    var bytes = Utilities.base64Decode(base64Data.split(',')[1]);
    var blob = Utilities.newBlob(bytes, mimeType, prefix + "_" + fileName);
    var file = folder.createFile(blob);
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    return "https://drive.google.com/uc?export=download&id=" + file.getId();
  } catch(e) { return ""; }
}

function getOrCreateFolder(name) {
  var folders = DriveApp.getFoldersByName(name);
  return folders.hasNext() ? folders.next() : DriveApp.createFolder(name);
}

function getCategories() {
  try {
    var data = getSheet('Categorias').getDataRange().getValues();
    data.shift();
    return data.map(function(r){ return r[0]; }).filter(function(c){ return c; });
  } catch(e) { return ["Geral"]; }
}

function getResponsaveis() {
  try {
    var data = getSheet('Responsaveis').getDataRange().getValues();
    data.shift();
    return data.map(function(r){ return r[0]; }).filter(function(r){ return r; });
  } catch(e) { return ["Walace", "Totvs"]; }
}

function saveConsultantResponse(id, texto, imgData, imgName, mimeType) {
  try {
    var sheet = getSheet('Topicos');
    var data = sheet.getDataRange().getValues();
    for (var i = 1; i < data.length; i++) {
      if (data[i][0].toString().trim() === id) {
        var row = i + 1;
        var imgUrl = "";
        if (imgData) imgUrl = saveToDrive(imgData, imgName, mimeType, "Solucao_" + id);
        sheet.getRange(row, 5).setValue('Concluida');
        sheet.getRange(row, 10).setValue(texto); // Col J (Solução)
        if (imgUrl) sheet.getRange(row, 11).setValue(imgUrl); // Col K (Img Solução)
        SpreadsheetApp.flush();
        return { success: true };
      }
    }
  } catch(e) { return { success: false, error: e.toString() }; }
}
