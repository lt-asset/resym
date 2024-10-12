#include <clang/AST/ASTConsumer.h>
#include <clang/AST/RecursiveASTVisitor.h>
#include <clang/Basic/Diagnostic.h>
#include <clang/Basic/FileManager.h>
#include <clang/Basic/SourceManager.h>
#include <clang/Basic/TargetInfo.h>
#include <clang/Basic/TargetOptions.h>
#include <clang/Frontend/CompilerInstance.h>
#include <clang/Frontend/FrontendAction.h>
#include <clang/Lex/Preprocessor.h>
#include <clang/Parse/ParseAST.h>
#include <clang/Rewrite/Core/Rewriter.h>
#include <clang/Rewrite/Frontend/Rewriters.h>
#include <clang/Tooling/Tooling.h>

#include "macros.hh"
#include "compilerUtils.hh"
#include "consumer.hh"
#include <fstream>
#include <iostream>
#include <llvm/Support/Host.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/Support/FileSystem.h>

#include <regex>
#include <sstream>
#include <string>

#undef DEBUG

using namespace clang;
using namespace std;





int main(int argc, char **argv) {
  if (argc < 3) {
    cout << "Usage: ./field_access <infile> <outfile>" << endl;
    return 1;
  }

  string infile = argv[1];
  string outfile = argv[2];

  CompilerInstance theCompiler;
  createCompilerInstance(theCompiler, infile);
  Rewriter rewriter = createRewriter(theCompiler);



  MyFieldAccessConsumer consumer(theCompiler.getASTContext(), rewriter);
  consumeAST(theCompiler, consumer);
  consumer.dumpAccessToJson(outfile);
  return 0;
}


