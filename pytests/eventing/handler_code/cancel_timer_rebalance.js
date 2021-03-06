function OnUpdate(doc, meta) {
    var expiry = new Date();
    expiry.setSeconds(expiry.getSeconds() + 3000);
    var context = {docID : meta.id, random_text : "e6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh0R7Aumoe6cZZGHuh07Aumoe6cZZGHuh07Aumoe6cZZGHuh07Aumoe6"};
    createTimer(timerCallback,  expiry, meta.id, context);
    log("create timer for:",meta.id)
}
function OnDelete(meta) {
    var context = {docID : meta.id};
    var cancelled=cancelTimer(timerCallback,meta.id);
    log("is timer cancelled:",cancelled," for:",meta.id);
    dst_bucket[meta.id]=meta.id;
}

function NDtimerCallback(context) {
    log("firing delete timer:",context.docID);
    var docID = context.docID;
    while (true) {
    try {
        delete dst_bucket[context.docID];
        break;
    } catch (e) {
        log(e);
        }
    }
}

function timerCallback(context) {
    log("firing update timer:",context.docID);
    var docID = context.docID;
    while (true) {
    try {
        dst_bucket[context.docID]=context.random_text;
        break;
    } catch (e) {
        log(e);
        }
    }
}
