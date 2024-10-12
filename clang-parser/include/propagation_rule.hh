#ifndef PROPAGATION_RULE_HH
#define PROPAGATION_RULE_HH


#include <string>
#include <unordered_map>


#include "clang/AST/ASTContext.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Lex/Lexer.h"
#include "macros.hh"
#include <iostream>
#include <nlohmann/json.hpp>



using namespace clang;
using namespace std;


struct FieldAccessInfo;
void to_json(nlohmann::json &j, const FieldAccessInfo &info);


class FieldAccessVisitor : public RecursiveASTVisitor<FieldAccessVisitor> {
public: 
    FieldAccessVisitor(ASTContext &C, Rewriter &R);
    ~FieldAccessVisitor();
    vector<FieldAccessInfo*> memberAccess;
    bool VisitBinaryOperator(BinaryOperator *expr);
    bool VisitArraySubscriptExpr(ArraySubscriptExpr *ase);
    bool VisitDeclRefExpr(DeclRefExpr *dref);
    nlohmann::json dumpAccessToJson();
private: 
    Rewriter &rewriter;
    ASTContext &context;
    unsigned getLineNumber(Expr *expr);
    bool isDeclArg(DeclRefExpr *dref);
    bool isExprPtr(DeclRefExpr *expr);
    bool isExprPtr(CStyleCastExpr *expr);
    bool isExprPtr(const CStyleCastExpr *expr);
    unsigned getTypeSizeInBytes(DeclRefExpr *dref);
    unsigned getTypeSizeInBytes(CStyleCastExpr *expr);
    unsigned getTypeSizeInBytesHelper(QualType qt);
    unsigned getPointeeSizeInBytes(DeclRefExpr *dref);
    unsigned getPointeeSizeInBytes(CStyleCastExpr *expr);
    unsigned getPointeeSizeInBytes(const CStyleCastExpr *expr);
    unsigned getPointeeSizeInBytesHelper(QualType qt);
    const CStyleCastExpr* getParentCastExpr(Expr *expr);
    FieldAccessInfo* parse_addition(BinaryOperator *bo);
    pair<unsigned, string> getExprPointeeDetails(const Expr *expr);
    pair<unsigned, string> getExprPointeeDetails(BinaryOperator *bo);
    bool isAddSubMulDivBinaryOp(const Stmt* stmt);
}; 



#endif