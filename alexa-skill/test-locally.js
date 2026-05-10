#!/usr/bin/env node
'use strict';

// Usage:
//   node test-locally.js --book genesis --startc 7 --startv 3 --endv 8
//   node test-locally.js --book numbers --startc 7 --startv 80 --endc 7 --endv 89
//   node test-locally.js --launch
//   node test-locally.js --parsha Bereishit

const handler = require('./index');

function usage() {
  console.error(`Usage:
  node test-locally.js --book <name> --startc <n> --startv <n> --endv <n> [--endc <n>]
  node test-locally.js --launch
  node test-locally.js --parsha <name>`);
  process.exit(1);
}

const args = process.argv.slice(2);
const get = (flag) => {
  const i = args.indexOf(flag);
  return i !== -1 ? args[i + 1] : undefined;
};
const has = (flag) => args.includes(flag);

let event;

if (has('--launch')) {
  event = {
    version: '1.0',
    session: { new: true, sessionId: 'local-test', attributes: {}, user: { userId: 'local' }, application: { applicationId: 'local' } },
    request: { type: 'LaunchRequest', requestId: 'local-req' }
  };
} else if (has('--parsha')) {
  const parsha = get('--parsha');
  event = {
    version: '1.0',
    session: { new: false, sessionId: 'local-test', attributes: {}, user: { userId: 'local' }, application: { applicationId: 'local' } },
    request: {
      type: 'IntentRequest',
      requestId: 'local-req',
      intent: {
        name: 'WhenIsParshaReadIntent',
        slots: { Parsha: { name: 'Parsha', value: parsha } }
      }
    }
  };
} else {
  const book   = get('--book');
  const startc = get('--startc');
  const startv = get('--startv');
  const endv   = get('--endv');
  const endc   = get('--endc');

  if (!book || !startc || !startv || !endv) usage();

  event = {
    version: '1.0',
    session: { new: false, sessionId: 'local-test', attributes: {}, user: { userId: 'local' }, application: { applicationId: 'local' } },
    request: {
      type: 'IntentRequest',
      requestId: 'local-req',
      intent: {
        name: 'ChantIntent',
        slots: {
          TorahBooks:   { name: 'TorahBooks',   value: book },
          StartChapter: { name: 'StartChapter', value: parseInt(startc, 10) },
          StartVerse:   { name: 'StartVerse',   value: parseInt(startv, 10) },
          EndChapter:   { name: 'EndChapter',   value: endc ? parseInt(endc, 10) : undefined },
          EndVerse:     { name: 'EndVerse',     value: parseInt(endv, 10) }
        }
      }
    }
  };
}

const context = {
  succeed: (response) => {
    const r = response.response;
    console.log('\n--- Speech ---');
    console.log(r.outputSpeech.ssml.replace(/<[^>]+>/g, '').trim());
    if (r.card) {
      console.log('\n--- Card ---');
      console.log('Title:', r.card.title);
      if (r.card.text)    console.log('Text:', r.card.text);
      if (r.card.content) console.log('Content:', r.card.content);
      if (r.card.image)   console.log('Image:', r.card.image.smallImageUrl);
    }
    const ssml = r.outputSpeech.ssml;
    const audioUrls = [...ssml.matchAll(/<audio src="([^"]+)"/g)].map(m => m[1]);
    if (audioUrls.length) {
      console.log('\n--- Audio URLs ---');
      audioUrls.forEach(u => console.log(u));
    }
    console.log('\n--- Full response JSON ---');
    console.log(JSON.stringify(response, null, 2));
  },
  fail: (err) => {
    console.error('Handler failed:', err);
    process.exit(1);
  }
};

process.env.NODE_DEBUG_EN = '';
handler.handler(event, context);
