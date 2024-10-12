#include "compilerUtils.hh"
// #include "ast_visitor_interface.hh"

using namespace clang;
using namespace std;


// define createCompilerInstance
void createCompilerInstance(CompilerInstance &theCompiler,
                            const string &filename) {
  theCompiler.createDiagnostics();
  auto &options = theCompiler.getLangOpts();
  options.C17 = true;
  auto targetOptions = std::make_shared<TargetOptions>();
  targetOptions->Triple = llvm::sys::getDefaultTargetTriple();
  TargetInfo *targetInfo =
      TargetInfo::CreateTargetInfo(theCompiler.getDiagnostics(), targetOptions);
  theCompiler.setTarget(targetInfo);
  theCompiler.createFileManager();
  auto &fileMgr = theCompiler.getFileManager();
  theCompiler.createSourceManager(fileMgr);
  auto &sourceMgr = theCompiler.getSourceManager();
  theCompiler.createPreprocessor(TU_Module);
  theCompiler.createASTContext();
  const FileEntry *srcFile = fileMgr.getFile(filename).get();
  auto &srcMgr = theCompiler.getSourceManager();
  srcMgr.setMainFileID(
      srcMgr.createFileID(srcFile, SourceLocation(), clang::SrcMgr::C_User));
  theCompiler.getDiagnosticClient().BeginSourceFile(
      options, &theCompiler.getPreprocessor());
  theCompiler.getLangOpts().CommentOpts.ParseAllComments = true;
}

Rewriter createRewriter(CompilerInstance &theCompiler) {
  Rewriter rewriter;
  rewriter.setSourceMgr(theCompiler.getSourceManager(),
                        theCompiler.getLangOpts());
  return rewriter;
}

void consumeAST(CompilerInstance &CI, MyConsumer &consumer) {
  ParseAST(CI.getPreprocessor(), &consumer, CI.getASTContext());
}


bool writeRewriterOutputToFile(Rewriter& rewriter, const string& filename) {
    error_code EC;
    llvm::raw_fd_ostream Out(filename, EC, llvm::sys::fs::OF_Text);
    if (EC) {
        llvm::errs() << "Error opening " << filename << " for writing: " << EC.message() << "\n";
        return false; // Indicate failure
    }
    rewriter.getEditBuffer(rewriter.getSourceMgr().getMainFileID()).write(Out);
    Out.close();
    return true; // Indicate success
}
