"""

strings_XX.txt gets out of date very quickly, especially when coding... it's not easy to keep track of what changes were made which require localization

*** THIS CODE ISN'T MEANT TO BE PRETTY, IT IS MEANT TO JUST WORK ***
I'm absolutely sure this code is sloppy... lol



So, this is to auto-generate strings.txt


This was some basic research, before going all Python

findstr /l /s "CNLS::GetString" *.cpp *.h

exceptions:
GetTooltip in NavigationPanel.cpp

REM search for what you forgot to localize:
findstr /s /l "_T" *.cpp *.h | findstr /v /l "CNLS::GetString"

"""
import re
from pathlib import Path
from datetime import datetime, timezone
import pprint

SOURCE_DIR = Path(__file__).resolve().parent.parent.parent / r"src\JPEGView"

#################################################################################################


def get_all_text_between(filepath, pattern_begin, pattern_end):

    if not filepath.exists():
        raise FileNotFoundError

    with open(filepath, 'r') as f:
        m = re.search(f"{pattern_begin}(.*?){pattern_end}", f.read(), re.MULTILINE | re.DOTALL)
        if m is None:
            raise LookupError(f"ERROR: couldn't find {pattern_begin}")

        # remove the len(pattern_end)
        return m.group(0)[:-len(pattern_end)]


#################################################################################################


def find_all_pattern(pattern, file_list=None, use_sets=False):
    """ find all strings with some pattern like _T(""), return dict

    file_list past in a list... [one file] works too

    use_sets uses sets to make sure what goes in the value of dict is a unique list
    """

    if file_list is None:
        # https://stackoverflow.com/questions/48181073/how-to-glob-two-patterns-with-pathlib/57893015#57893015
        exts = [".h", ".cpp"]
        files = [p for p in Path(SOURCE_DIR).rglob('*') if p.suffix in exts]
    else:
        files = file_list

    #print(list(files))

    list_all = {}

    for f in files:
        # search the file for patterns
        for s in re.findall(pattern, f.read_text()):
            # to figure out what file it came from
            if s in list_all:
                if use_sets:
                    list_all[s].add(f)
                else:
                    list_all[s].append(f)

            else:
                if use_sets:
                    list_all[s] = {f}
                else:
                    list_all[s] = [f]

    return list_all


#################################################################################################


def search_untranslated_strings(translated_t_dict):
    """
    look for _T() which are not translated, to see if they should be translated
    """

    # find all places where there is a string
    all_t = find_all_pattern(r'_T\s*\(\s*"(.*?)"\s*\)', use_sets=True)  # we don't need to know that it shows up multiple times in a file for this routine

    # remove the known translated ones from all_t
    # to show what strings are NOT translated (at least in theory, since var_cnls_no_t might do it)
    for x in translated_t_dict.keys():
        del all_t[x]  # this should never throw an error as the patterns overlap


    # manual patterns to remove to make list more manageable
    temp_dict = all_t.copy()  # so we don't get a changing-while-reading error
    for k, v in temp_dict.items():
        # delete empty strings, or those which are empty after strip()
        if k.strip() == "":
            pass

        # extension strings, aka ".jpg"
        elif re.fullmatch("\.[a-z]{3}", k):
            pass

        # any strings of "*.ext" or "*.ext2"
        elif re.fullmatch("\*\.[a-z]{3,4}", k):
            pass

        # ignore strings of all symbols
        elif re.fullmatch("[\W]+", k):
            pass

        # ignore all numbers
        elif re.fullmatch("[\d\.]+", k):
            pass

        # begins and ends with <>
        elif k.startswith("<") and k.endswith(">"):
            pass

        # begins and ends with %
        elif k.startswith("%") and k.endswith("%"):
            pass

        # begins and ends with {}
        elif k.startswith("{") and k.endswith("}"):
            pass

        # ignore the ones that start with a / (command line params)
        elif k.startswith("/"):
            pass

        elif k.startswith("JPEGView"):
            pass

        # if string only exists in SettingsProvider
        elif len(v) == 1 and (SOURCE_DIR / "SettingsProvider.cpp") in v:
            pass

        # if string only exists in KeyMap
        elif len(v) == 1 and (SOURCE_DIR / "KeyMap.cpp") in v:
            pass

        # not enough characters, only one character in string
        elif not re.search("[a-zA-Z]{2}", k):
            pass

        else:
            # due to the logic above using pass, this has to skip the stuff below
            continue


        print(f"_T IGNORED: {k}")
        del all_t[k]




    # fixed things we are deleting, known not to need translation, list built by hand
    remove_from_all_t = [
        '%%%cx', '%%.%df', '%%0%cd', '%Nx : ', '%d KB', '%d MB', '%h %min : ', '%lf', '%min', '%pictures% : ',
        'rb',
    ]

    for x in remove_from_all_t:
        print(f"_T IGNORED: {k}")
        del all_t[x]

    return all_t


#################################################################################################


def parse_popup_menu_resource():
    """
    parse for strings in the resource's MENUs, as this doesn't match the _T() pattern
    """

    # this matches the popup menu pattern in source!
    menu_code = get_all_text_between(SOURCE_DIR / "JPEGView.rc", "POPUPMENU MENU", "//////////")

    #print(menu_code)

    # counter to ignore a certain count of lines after a certain trigger
    ignore_lines = 0

    # i don't use a set here because i want the menu items ordered the way they are listed... sets are unordered, and i don't want to sort the list
    ret_list = []

    for line in menu_code.split("\n"):
        line = line.strip()  # remove any leading or trailing whitespace

        if ignore_lines != 0:
            ignore_lines -= 1
            continue

        if re.fullmatch("[A-Z]+MENU MENU", line):  # this is a pattern that the code uses... ALL CAPS, then the word MENU, then the actual keyword MENU... after this, the first name POPUP "" does not need to be translated
            ignore_lines = 2
            continue

        # in any other case, seach for the general pattern, ignore all others
        # basically, just look for quotes
        if line.find('"') != -1:
            # NOTE: this MAY fail if you have "'s in the string, like \" or something... right now we don't have any, and we shouldn't have any in menus, but this code does NOT accommodate for that!
            m = re.search('"(.+)"', line)
            quote_str = m.group(1)  # get string in quotes

            # ignore certain patterns
            if quote_str == "_empty_":
                print(f"MENU IGNORED: {quote_str}")
                continue
            elif re.search("[a-zA-Z]{2}", quote_str) is None:
                # ignore lines where there's no contiguous characters to translate
                print(f"MENU IGNORED: {quote_str}")
                continue

            if "\\t" in quote_str:
                # special handling if there's a \t sequence as it means something different
                (first_part, second_part) = quote_str.split("\\t")  # it only splits into two

                # add the first part
                if first_part not in ret_list:
                    ret_list.append(first_part)

                if second_part.startswith("0x"):
                    print(f"MENU \\t IGNORED: {second_part}")
                    continue
                elif second_part == "Esc":
                    # special key sequence to ignore
                    print(f"MENU \\t IGNORED: {second_part}")
                    continue

                if second_part not in ret_list:
                    ret_list.append(second_part)

            else:
                if quote_str not in ret_list:
                    ret_list.append(quote_str)

    return ret_list


#################################################################################################



def dump_strings_txt(sorted_strings_dict, menu_list):
    """

    """
    menu_strings = menu_list.copy()  # because we're modifying it later

    OUT_FILE = SOURCE_DIR / "Config" / "strings.txt"

    # dump the dict out

    # UPDATE THE LASTUPDATED if this text gets updated so we know when translations are out of date!
    with open(OUT_FILE, 'wt', encoding='utf-8') as f:
        f.write(f"""// STRINGS.TXT REFERENCE FILE: make a copy, remove this line, and follow the instructions to add/update languages -- Autogenerated, Last Updated: {datetime.now(timezone.utc).isoformat()}

// This file must be encoded with UTF-8 (e.g. with Windows Notepad)
// Filename Convention: 'strings_%languagecode%.txt' where %languagecode% is the ISO 639 language code e.g. 'fr' for French

////////////////////
// Line Format:   English string<tab>Translated string<newline>
// * Lines beginning with "//" are ignored
// * Blank lines are ignored
// * Lines without a <tab> or have no text after the tab are ignored

// NOTE: %s %d have special meanings in the strings, so make sure they appear somewhere in the translated string
//
// For the strings below which are short and have no context:
//   "in" in context is shorthand for "inch"
//   "cm" in context is shorthand for "centimeter"
//   "C - R" in context is "Cyan Red" colors
//   "M - G" in context is "Magenta Green" colors
//   "Y - B" in context is "Yellow Blue" colors
//   "yes"/"no" in context for showing EXIF flags
//   "on"/"off" in context for showing a setting active or not
////////////////////

////////////////////
// == Translator Credits ==
// Language: English
// Translator Name(s) / Contact(s):
// History/Notes:
// Last Updated:
////////////////////

// ::: Program Strings ::: (sorted alphabetically) //
""")
        keys = list(sorted_strings_dict.keys())
        #keys.sort(key=str.casefold)  # case-insensitive
        keys.sort()  # leave it case sensitive, as the lower case is easy to reference for "in" and "cm"
        for k in keys:
            #f.write(f"{k}\t{k}\n")  # sample just has string<tab>string
            f.write(f"{k}\t\n")  # sample with string<tab>string is hard to translate and fill in

            # do you want to know what file(s) the string came from?  for debugging only
            #f.write(f"{k}\t{d[k]}\n")

            # remove this entry if it exists in the menu strings (so there's no duplicate translation strings)
            try:
                menu_strings.remove(k)
                print(f"Duplicate string from menu removed: {k}")
            except ValueError:
                pass

        f.write("""
// ::: Popup Menu Strings ::: (unsorted to preserve context) //
""")
        # these aren't sorted alphabetically, for clarity (and context)
        for k in menu_strings:
            #f.write(f"{k}\t{k}\n")  # sample just has string<tab>string
            f.write(f"{k}\t\n")  # string<tab>string too hard to find diffs or untranslated text



if __name__ == "__main__":

    all_cnls_t = find_all_pattern(r'CNLS::GetString\s*\(\s*_T\s*\(\s*"(.*?)"\s*\)\s*\)')

    # exception in this particular function call
    all_cnls_t.update(find_all_pattern(r'GetTooltip\(\w+,\s*_T\s*\(\s*"(.*?)"\s*\)', [SOURCE_DIR / "NavigationPanel.cpp"]))


    # these are also special, in that it's translated by HelpersGUI.cpp =>  CNLS::GetString(menuText)
    popup_list = parse_popup_menu_resource()

    #pprint.pprint(popup_list)


    #print(all_cnls_t)
    dump_strings_txt(all_cnls_t, popup_list)


    all_t = search_untranslated_strings(all_cnls_t)

    print(f"{'!' * 30} NOT TRANSLATED {'!' * 30}")
    pprint.pprint(all_t)
    # ----------------------------------------------------------------------------------------



    # find places where GetString is used without _T, meaning it's of a variable
    print()
    print(f"{'~' * 30} GetString() without _T() {'~' * 30}")
    var_cnls_no_t = find_all_pattern(r'CNLS::GetString\s*\(\s*([^_].*?)\s*\)', use_sets=True)
    pprint.pprint(var_cnls_no_t)
    # one of the places is in the INI there is Help Text= '' for usercommand... this is fed into translation... confirmation is as well
