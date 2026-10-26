/** Separate test bridge; doesn't alter existing 20-Win tracker. */
function github20WinPayload_(entry, previewOnly) {
  function playerPart(p) {
    return {
      name: String(p.name || 'Unknown'),
      clan: {name: String((p.clan || {}).name || '')},
      cards: (p.cards || []).slice(0, 8).map(function(c) {
        return {
          name: String(c.name || ''),
          iconUrls: {
            medium: String((c.iconUrls || {}).medium || ''),
            evolutionMedium: String((c.iconUrls || {}).evolutionMedium || '')
          },
          evolutionLevel: Number(c.evolutionLevel || 0)
        };
      })
    };
  }
  return {
    milestone: Number(entry.milestone),
    crownsFor: Number(entry.crownsFor || 0),
    crownsAgainst: Number(entry.crownsAgainst || 0),
    player: playerPart(entry.player),
    opponent: playerPart(entry.opponent),
    previewOnly: previewOnly === true
  };
}

function dispatch20WinToGithub_(entry, previewOnly) {
  const props = PropertiesService.getScriptProperties();
  const repo = props.getProperty('CRL_GITHUB_REPO'); // owner/repository
  const token = props.getProperty('CRL_GITHUB_TOKEN');
  if (!repo || !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo)) {
    throw new Error('Set CRL_GITHUB_REPO to your-user/crl-battle-renderer');
  }
  if (!token) throw new Error('Missing CRL_GITHUB_TOKEN script property');

  const url = 'https://api.github.com/repos/' + repo + '/dispatches';
  const res = UrlFetchApp.fetch(url, {
    method: 'post',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'CRL-Battle-Tracker'
    },
    contentType: 'application/json',
    payload: JSON.stringify({
      event_type: 'crl-battle',
      client_payload: github20WinPayload_(entry, previewOnly)
    }),
    muteHttpExceptions: true
  });
  if (res.getResponseCode() !== 204) {
    throw new Error('GitHub dispatch HTTP ' + res.getResponseCode() + ': ' + res.getContentText());
  }
  console.log('GitHub accepted render job. View repo Actions tab.');
}

/** First test: generate downloadable image in GitHub Actions; no Discord post. */
function previewSaved20WinOnGithub() {
  const saved = PropertiesService.getScriptProperties().getProperty('20_WIN_TEST_BATTLE');
  if (!saved) throw new Error('20_WIN_TEST_BATTLE is missing from Script Properties');
  dispatch20WinToGithub_(JSON.parse(saved), true);
}

/** After inspecting image AND verifying GitHub webhook secret, posts exactly one Vitor test. */
function postSaved20WinFromGithub() {
  const saved = PropertiesService.getScriptProperties().getProperty('20_WIN_TEST_BATTLE');
  if (!saved) throw new Error('20_WIN_TEST_BATTLE is missing from Script Properties');
  dispatch20WinToGithub_(JSON.parse(saved), false);
}
