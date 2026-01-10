const vscode = require('vscode');
const { LanguageClient, TransportKind } = require('vscode-languageclient/node');

let client;

function activate(context) {
    const config = vscode.workspace.getConfiguration('zero.lsp');

    if (!config.get('enabled', true)) {
        return;
    }

    const command = config.get('command', ['uv', 'run', 'python', '-m', 'zero.lsp']);
    const [cmd, ...args] = command;

    const serverOptions = {
        command: cmd,
        args: args,
        options: {
            cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath
        }
    };

    const clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'zero' }],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.zr')
        }
    };

    client = new LanguageClient(
        'zeroLanguageServer',
        'Zero Language Server',
        serverOptions,
        clientOptions
    );

    client.start();
}

function deactivate() {
    if (client) {
        return client.stop();
    }
}

module.exports = { activate, deactivate };
