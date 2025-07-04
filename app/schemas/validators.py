# def protection_against_xss(value: str) -> str:
#     forbidden_char = ["<", ">", "/"]
#     for i in value:
#         if i in forbidden_char:
#             raise ValueError(
#                 f"These characthers are forbidden: {', '.join(forbidden_char)}"
#             )
#     return value
