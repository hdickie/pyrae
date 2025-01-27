import re
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from bs4.element import Tag
from copy import deepcopy
from typing import List, Optional, Sequence, Union

DLE_MAIN_URL = 'https://dle.rae.es'

class FromHTML(ABC):
    """ Represents an entity that can parse HTML text.
    """
    def __init__(self, html: str):
        """ Initializes a new instance of the FromHTML class.

        :param html: HTML text.
        """

        self._parsed: bool = False
        self._raw_text: str = ''
        self._soup: Optional[BeautifulSoup] = None

        self.html = html

    def __getstate__(self) -> dict:
        """ Gets a dictionary with attributes that are pickable.

        :return: A dictionary with attributes that are pickable.
        """
        state = self.__dict__.copy()
        # Remove the unpickable entries.
        if '_soup' in state:
            del state['_soup']
        return state

    def __setstate__(self, state):
        """ Restores instance attributes after unpickling.

        :param state: A saved instance state.
        """
        self.__dict__.update(state)
        self._soup: Optional[BeautifulSoup] = None
        self._parse_html()

    @property
    def html(self) -> str:
        """ Gets the HTML text used for parsing.
        """
        return self._html

    @html.setter
    def html(self, value: str):
        """ Property setter for html.

        :param value: The HTML text used for parsing.
        """

        self._html = value
        self._parsed = False
        self._parse_html()

    @classmethod
    def from_html(cls, html: str):
        """ Creates an instance from HTML code if parsed successfully.
        """
        try:
            return cls(html=html)
        except Exception:
            return None


    @abstractmethod
    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        return {
            'html': self._html
        } if extended else {}

    @abstractmethod
    def _parse_html(self):
        """ Parses the contents of the HTML.
        """

        if not self._html:
            raise Exception('No HTML has been set.')
        if not re.search(pattern='<[^>]*>', string=str(self._html)):
            raise Exception('No HTML text to parse.')
        self._soup = BeautifulSoup(self._html, 'html.parser')
        if not self._soup:
            raise Exception('Invalid HTML.')

    @abstractmethod
    def _reset(self):
        """ Resets fields to a clean state. Needed when resetting the HTML text.
        """
        pass


class Abbr(FromHTML):
    """ Represents an abbreviation.
    """
    def __init__(self, html: str):
        """ Initializes a new instance of the Abbr class.

        :param html: HTML code that represents an abbreviation.
        """
        super().__init__(html=html)


    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Abbr(abbr="{self._abbr}", class="{self._class}", text="{self._text}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'{self._abbr} ({self._text})'

    @property
    def abbr(self) -> str:
        """ Gets the abbreviated text.
        """
        return self._abbr

    @property
    def class_(self) -> str:
        """ Gets the class of the abbreviation (if any).
        """
        return self._class

    @property
    def text(self) -> str:
        """ Gets the expanded text for the abbreviation.
        """
        return self._text

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict['abbr'] = self._abbr
        if extended:
            res_dict['class'] = self._class
        res_dict['text'] = self._text
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()

        if self._parsed:
            return
        self._reset()

        if not self._soup.abbr:
            raise Exception('Invalid HTML.')
        self._abbr = self._soup.abbr.text
        if self._soup.abbr.has_attr('class'):
            self._class = self._soup.abbr['class'][0]
        if not self._soup.abbr.has_attr('title'):
            raise Exception('The title attribute is expected to contain the expanded text.')
        self._text = self._soup.abbr['title']
        self._parsed = True

    def _reset(self):
        """ Resets fields to a clean state. Needed when resetting the HTML text.
        """
        self._abbr: str = ''
        self._class: str = ''
        self._text: str = ''


class Word(FromHTML):
    """ A single word with a corresponding ID in the RAE dictionary.
    """
    def __init__(self, html: str,
                 parent_href: str = ''):
        """ Initialize a new instance of the Word class.

        :param html: HTML code that represents a single word.
        :param parent_href: An optional HREF to complement the link if needed.
        """
        self._parent_href: str = parent_href
        super().__init__(html=html)


    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Word(text="{self._text}", active_link={self._is_active_link}, ' \
               f'html="{self._html}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._text

    @property
    def href(self) -> str:
        """ Gets a HREF piece of the link corresponding to this word.
        """
        return self._href

    @property
    def is_active_link(self) -> bool:
        """ Gets a value indicating whether the word is part of an active link, meaning RAE rendered this
        word with an <a> element so the reader sees the word as a regular hyperlink. When not an active
        link, RAE renders the word with a <mark> element so the word is render normally but still can be
        clicked to search for its meaning.
        """
        return self._is_active_link

    @property
    def link(self) -> str:
        """ Gets the link to get results for this word.
        """
        return f'{DLE_MAIN_URL}{self._href}' if self._href else ''

    @property
    def text(self) -> str:
        """ Gets the text of the word.
        """
        return self._text

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict['text'] = self._text
        if self._is_active_link:
            res_dict['link'] = self.link
        if extended:
            res_dict['is_active_link'] = self._is_active_link
            if not self._is_active_link:
                res_dict['link'] = self.link
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()

        if self._parsed:
            return

        self._reset()

        for sup_tag in self._soup.find_all("sup"):
            sup_tag.decompose()

        if self._soup.mark:
            self._href = f"/?id={self._soup.mark['data-id']}"
            self._text = self._soup.mark.text
        elif self._soup.a:
            self._text = self._soup.a.text.strip()
            self._href = self._soup.a['href']
            if self._href and not self._href.startswith('/'):
                self._href = f'/{self._parent_href}{self._href}'
            self._is_active_link = True
        elif (self._soup.span
              and (self._soup.span['class'][0].lower() == 'u'
                   or 'data-id' in self._soup.span.attrs)):
            self._text = self._soup.span.text
        else:
            raise Exception('The HTML code cannot be parsed to a Word.')
        self._parsed = True


    def _reset(self):
        """ Resets fields to a clean state. Needed when resetting the HTML text.
        """
        self._text: str = ''
        self._href: str = ''
        self._is_active_link: bool = False


class Sentence(FromHTML):
    """ A sentence made up of strings and instances of the Word class.
    """
    def __init__(self, html: str,
                 ignore_tags: Sequence[str] = ()):
        """ Initializes a new instance of the Sentence class.

        :param html: HTML code that can be parsed into a sentence.
        :param ignore_tags: A sequence of tags to be ignored while parsing the sentence.
        """
        self._ignore_tags: Sequence[str] = ignore_tags
        super().__init__(html=html)


    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        # noinspection SpellCheckingInspection
        counts = {
            'abbrs': 0,
            'strings': 0,
            'words': 0
        }
        for component in self._components:
            if isinstance(component, Abbr):
                # noinspection SpellCheckingInspection
                counts['abbrs'] += 1
            elif isinstance(component, Word):
                counts['words'] += 1
            else:
                counts['strings'] += 1
        # noinspection SpellCheckingInspection
        return f'Sentence(text="{self.text}", abbrs={counts["abbrs"]}, words={counts["words"]}, ' \
               f'strings={counts["string"]})'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self.text

    @property
    def components(self) -> Sequence[Union[Abbr, Word, str]]:
        """ Gets the components of a sentence, can be strings or instances of the Word class.
        """
        return self._components

    @property
    def text(self) -> str:
        """ Gets the text of the sentence.
        """
        return ''.join([str(component) for component in self._components]).strip()

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict['text'] = self.text
        if extended:
            res_dict['components'] = [component.to_dict(extended=extended)
                                      if not isinstance(component, str) else component
                                      for component in self._components]
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()

        if self._parsed:
            return
        self._reset()

        for tag in self._soup.contents[0].children:
            if tag.name in self._ignore_tags:
                continue

            if tag.name == 'span' and 'data-id' not in tag.attrs:
                if tag.has_attr('class'):
                    #for spans in supp_info
                    # not sure if classes are general
                    if tag.name == 'span' and ('af' in tag['class'] #from guardia
                                               or 'u' in tag['class']): #from enferma
                        pass
                    else:
                        continue

            abbr = Abbr.from_html(html=str(tag))
            if abbr:
                self._components.append(abbr)
                continue
            word = Word.from_html(html=str(tag))
            if word:
                self._components.append(word)
                continue
            unwanted_abbreviations = [
                'And.',
                'Arg.',
                'Col.',
                'C. Rica',
                #'Chile.',
                'Cuba.',
                'Ec.',
                'El Salv.',
                'Guat.',
                'Hond.',
                'León.',
                'Mat.',
                'Méx.',
                'Mur.',
                'Nav.',
                'Nic.',
                'Pan.',
                'Par.',
                'Perú',
                'P. Rico.',
                'R. Dom.',
                'Ur.',
                'Ven.',

                'TV.',
                'Zool.',
                'Arq.',
                'Constr.',
                'Fotogr.',
                'Geol.',
                'Ling.',
                'Métr.',
                'Pint.',
                'Psiquiatr.',
                'Teatro.',

                '1.', #these are superscripts that are coming through
                '2.',
                '3.',
                '4.',

                'Med.'
            ]
            skip_ind = False
            for ua in unwanted_abbreviations:
                if str(tag).strip().endswith(ua):
                    skip_ind = True
                    break
            if skip_ind:
                continue
            self._components.append(tag.get_text() if isinstance(tag, Tag) else str(tag))
        self._parsed = True


    def _reset(self):
        """ Resets fields to a clean state. Needed when resetting the HTML text.
        """
        self._components: List[Union[Abbr, Word, str]] = []


class Definition(FromHTML):
    """ Represents a simple definition for a simple or complex form.
    """
    __INDEX_REGEX_STRING = r'^(?P<index>\d+).\D*$'
    # noinspection SpellCheckingInspection
    __VERB_REGEX_STRING = r'^.*verbo.*$'
    __index_re = re.compile(pattern=__INDEX_REGEX_STRING, flags=re.IGNORECASE)
    __verb_re = re.compile(pattern=__VERB_REGEX_STRING, flags=re.IGNORECASE)

    def __init__(self, html: str):
        """ Initializes a new instance of the Definition class.

        :param html: HTML code that contains a definition.
        """
        super().__init__(html=html)

    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Definition(id="{self._id}", raw_text="{self._raw_text}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._raw_text

    @property
    def abbreviations(self) -> Sequence[Abbr]:
        """ Gets a dictionary where its keys represent the abbreviations and its values, the full words.
        """
        return self._abbreviations

    @property
    def category(self) -> Abbr:
        """ Gets the abbreviation that represents the grammatical category of this definition.
        """
        return self._category

    @property
    def examples(self) -> Sequence[Sentence]:
        """ Gets a collection of sentences representing examples for this definition.
        """
        return self._examples

    @property
    def first_of_category(self) -> bool:
        """ Gets a value indicating whether the category is the first one in a block of grammatical categories.
        """
        return self._first_of_category

    @property
    def id(self) -> str:
        """ Gets the ID of the definition.
        """
        return self._id

    @property
    def index(self) -> int:
        """ Gets the ordinal index of this definition.
        """
        return self._index

    @property
    def is_adverb(self) -> bool:
        """ Gets a value indicating whether the category of the definition corresponds to an adverb.
        """
        return self._category.abbr == 'adv.'

    @property
    def is_adjective(self) -> bool:
        """ Gets a value indicating whether the category of the definition corresponds to an adjective.
        """
        return self._category.abbr == 'adj.'

    @property
    def is_interjection(self) -> bool:
        """ Gets a value indicating whether the category of the definition corresponds to an interjection.
        """
        return self._category.abbr == 'interj.'

    @property
    def is_noun(self) -> bool:
        """ Gets a value indicating whether the category of the definition corresponds to a noun.
        """
        # noinspection SpellCheckingInspection
        return self._category.abbr in ('s.', 'sust.', 'm.', 'f.', 'm. y f.')

    @property
    def is_pronoun(self) -> bool:
        """ Gets a value indicating whether the category of the definition corresponds to a pronoun.
        """
        return self._category.abbr == 'pron.'

    @property
    def is_verb(self) -> bool:
        """ Gets a value indicating whether the category of the definition corresponds to a verb.
        """
        # noinspection SpellCheckingInspection
        return (self.__verb_re.match(self._category.text) is not None
                or re.search(pattern='|'.join(('part.', 'ger.', 'pret.', 'fut.', 'pres.', 'infinit.')),
                             string=self._category.abbr) is not None)

    @property
    def raw_text(self) -> str:
        """ Gets the raw text of the whole HTML used for the definition.
        """
        return self._raw_text

    @property
    def sentence(self) -> Optional[Sentence]:
        """ Gets the main sentence of this definition.
        """
        return self._sentence

    @property
    def text(self) -> str:
        """ Gets the text of the main sentence of the definition.
        """
        return self._sentence.text if self._sentence else ''

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        if extended:
            res_dict['id'] = self._id
        res_dict.update({
            'index': self._index,
            'category': self._category.to_dict(extended=extended),
            'is': {
                'adjective': self.is_adjective,
                'adverb': self.is_adverb,
                'interjection': self.is_interjection,
                'noun': self.is_noun,
                'pronoun': self.is_pronoun,
                'verb': self.is_verb
            }
        })
        if extended:
            res_dict['first_of_category'] = self._first_of_category
        res_dict.update({
            'abbreviations': [abbr.to_dict(extended=extended) for abbr in self._abbreviations],
            'sentence': self._sentence.to_dict(extended=extended),
            'examples': [ex.to_dict(extended=extended) for ex in self._examples]
        })
        if extended:
            res_dict['raw_text'] = self._raw_text

        # print(self)
        if self._synonyms:
            res_dict['synonyms'] = self._synonyms
        if self._antonyms:
            res_dict['antonyms'] = self._antonyms

        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()

        if self._parsed:
            return
        self._reset()

        for tag in self._soup.find_all(['span','abbr']):
            if not isinstance(tag, Tag):
                continue


            tag_class = tag['class'][0].lower() if tag.has_attr('class') else ''
            if tag.name == 'span':
                # noinspection SpellCheckingInspection
                if tag_class == 'n_acep':
                    match = self.__index_re.match(string=tag.text)
                    if match:
                        self._index = int(match['index'])
                elif tag_class == 'h':
                    self._examples.append(Sentence(html=str(tag)))
            elif tag.name == 'abbr':
                if not self._category:
                    self._category = Abbr(html=str(tag))
                    self._first_of_category = tag_class == 'd'
                else:
                    if tag.text == 'Sin.:' or  tag.text == 'Ant.:':
                        continue

                    dont_append_this_one = False
                    if tag.has_attr('title'):
                        if tag['title'] == 'Ámbito del sentido':
                            dont_append_this_one = True

                    if tag.text.strip() == '' or tag.text.strip() == 'etc.' or tag.text.strip() == 'etc.,' or dont_append_this_one:
                        pass
                    else:
                        self._abbreviations.append(Abbr(html=str(tag)))

        raw_sentence = "<div> "
        root = self._soup.find('div', class_='c-definitions__item')
        ant_or_syn_word_type = None
        antonym_lists = []
        synonym_lists = []
        for elem in root.children:

            #this top level is always a div, but sometimes it has no class and sometimes it has
            # c-definitions__item-footer. which has Syn and Ant
            if elem.has_attr('class'):
                #Syn and Ant stuff
                if "c-definitions__item-footer" in elem["class"]:
                    for ant_or_syn_elem in elem.children:
                        if ant_or_syn_elem.has_attr("class"):
                            if "c-word-list" in  ant_or_syn_elem["class"]:
                                #expect a div saying syn or ant, then a ul
                                for ant_or_syn_elem2 in ant_or_syn_elem.children:
                                    if ant_or_syn_elem2.name == 'div':
                                        ant_or_syn_word_type = ant_or_syn_elem2.text.replace(':','')
                                    else:
                                        pass #each li is a comma separated list
                                        current_word_list = []
                                        for a_or_s in ant_or_syn_elem2.descendants:
                                            if a_or_s.name is None:
                                                a_or_s_text = a_or_s.text
                                                a_or_s_text = a_or_s_text.replace('.','').replace(',','').strip()

                                                #this is a lazy way to remove superscript numbers
                                                a_or_s_text = a_or_s_text.replace('1','').replace('2','').replace('3','')
                                                a_or_s_text = a_or_s_text.replace('4', '').replace('5', '').replace('6','')
                                                a_or_s_text = a_or_s_text.replace('7', '').replace('8', '').replace('9','')
                                                a_or_s_text = a_or_s_text.replace('0', '')
                                                if a_or_s_text != '':
                                                    current_word_list.append(a_or_s_text)
                                        if ant_or_syn_word_type == 'Sin.':
                                            synonym_lists.append(current_word_list)
                                        elif ant_or_syn_word_type == 'Ant.':
                                            antonym_lists.append(current_word_list)
            else:
                for elem2 in elem.children:
                    if elem2.name is None:
                        raw_sentence += elem2  #often punctuation and whitespace
                        continue
                    elif elem2.name == 'i':
                        for italicized_text in elem2.contents:
                            raw_sentence += " "+str(italicized_text.text)
                    elif elem2.name == 'a':
                        e2_c_keep = ""
                        for e2_c in elem2.contents:
                            if e2_c.name is None:
                                e2_c_keep += str(e2_c)
                            elif e2_c.name == 'i':
                                e2_c_keep += str(e2_c.text)
                        raw_sentence += e2_c_keep
                    elif elem2.name == 'span':
                        if elem2.has_attr('class'):
                            if "h" in elem2["class"]:
                                continue
                        raw_sentence += str(elem2) #index
                        continue
                    elif elem2.name == 'abbr':
                        if elem2.has_attr('class'):
                            if "d" in elem2['class'] \
                                    or "g" in elem2['class']: #part of speech
                                raw_sentence += " "+str(elem2) #part of speech
                                continue
                            if "c" in elem2['class']: #category abbr at start of def?
                                raw_sentence += " "+str(elem2)
                                continue
        raw_sentence += "</div>"

        self._synonyms = synonym_lists
        self._antonyms = antonym_lists

        self._sentence = Sentence(html=raw_sentence, ignore_tags=('abbr',))
        self._parsed = True

    def _reset(self):
        """ Resets fields to a clean state. Needed when resetting the HTML text.
        """
        self._id: str = ''
        self._index: int = 0
        self._category: Optional[Abbr] = None
        self._first_of_category: bool = False
        self._abbreviations: List[Abbr] = []
        self._sentence: Optional[Sentence] = None
        self._examples: List[Sentence] = []
        self._raw_text: str = ''


class EntryLema(FromHTML):
    """ Represents a lema for a simple entry.
    """
    PROCESSING_TAGS = {
        'lema': {
            'tag': 'p',
            'class': 'k'
        }
    }

    def __init__(self, html: str):
        """ Initializes a new instance of the EntryLema class.

        :param html: HTML code that contains a lema entry.
        """
        super().__init__(html=html)


    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Lema(id="{self._id}", lema="{self._lema}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._lema

    @property
    def id(self) -> str:
        """ Gets the ID (if any) associated to this lema.
        """
        return self._id

    @property
    def is_foreign(self) -> bool:
        """ Gets a value indicating whether the lema word is of foreign origin or of a non-adapted latin origin.
        """
        return self._is_foreign

    @property
    def lema(self) -> str:
        """ Gets the lema word.
        """
        return self._lema

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict['lema'] = self._lema
        if extended:
            res_dict.update({
                'id': self._id,
                'is_foreign': self._is_foreign
            })
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()

        if self._parsed:
            return

        self._reset()

        tag = self._soup.find(name='h1')
        if not tag:
            tag = self._soup.find(name='h3')

        if tag.has_attr('id'):
            self._id = tag['id']
        self._lema = tag.get_text().strip()

        #There were no i tags and i couldn't tell where one would go
        #self._is_foreign = tag.find(name='i') is not None #old line; I can't tell what this does from my examples.
        self._is_foreign = False
        self._parsed = True

    def _reset(self):
        """ Resets fields to a clean state. Needed when resetting the HTML text.
        """
        self._id: str = ''
        self._is_foreign: bool = False
        self._lema: str = ''


class Entry(FromHTML):
    """ Represents an entry, which is a full group of definitions for a word or word combination.
    """
    _LEMA_CLASS = EntryLema
    PROCESSING_TAGS = {
        'supplementary_info': {
            'tag': 'p',
            'class': 'n'
        },
        'definition': {
            'tag': 'p',
            'class': 'm'
        }
    }

    def __init__(self, html: str):
        """ Initializes a new instance of the Entry class.

        :param html: HTML code that contains a simple entry.
        """
        super().__init__(html=html)


    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Entry(lema="{self.lema.lema}", raw_text="{self._raw_text}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._raw_text

    @property
    def definitions(self) -> List[Definition]:
        """ Gets a collection of definitions (simple forms) for the lema word.
        """
        return self._definitions

    @property
    def lema(self) -> EntryLema:
        """ Gets the lema for this entry.
        """
        return self._lema

    @property
    def raw_text(self) -> str:
        """ Gets the raw text of the whole HTML used for the Article.
        """
        return self._raw_text

    @property
    def supplementary_info(self) -> List[Sentence]:
        """ Gets a collection (if any) of supplementary information about the lema word.
        """
        return self._supplementary_info

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict.update({
            'lema': self.lema.to_dict(extended=extended),
            'supplementary_info': [s.to_dict(extended=extended) for s in self._supplementary_info],
            'definitions': [definition.to_dict(extended=extended) for definition in self._definitions]
        })
        if extended:
            res_dict['raw_text'] = self._raw_text
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()

        if self._parsed:
            return
        self._reset()
        self._process_entry(entry_tag=self._soup.contents[0])
        self._parsed = True


    def _process_entry(self, entry_tag: Tag):
        """ Processes the whole entry.

        :param entry_tag: A tag instance.
        """
        if not entry_tag:
            return

        for tag in entry_tag.children:
            if not isinstance(tag, Tag):
                continue
            if not self._lema:
                self._lema = self._LEMA_CLASS.from_html(html=str(tag))
                if self._lema:
                    continue

            pass
            class_letter = tag['class'][0].lower()[0] if tag.has_attr('class') else ''
            if (tag.name == 'li' and class_letter == 'j') \
                    or (tag.name == 'li' and class_letter == 'm'):
                self._definitions.append(Definition(html=str(tag)))
            elif (tag.name == 'div' and class_letter == 'n'): #real class here is n2 but it should be fine
                self._supplementary_info.append(Sentence(html=str(tag)))

        if not self._lema:
            raise Exception('Could not process lema from the given HTML.')
        self._raw_text = self._soup.get_text()


    def _reset(self):
        """ Resets fields to a clean state. Needed when resetting the HTML text.
        """
        self._lema: Optional[EntryLema] = None
        self._supplementary_info: List[Sentence] = []
        self._definitions: List[Definition] = []
        self._raw_text: str = ''


class ArticleLema(EntryLema):
    """ Represents a lema for an article.
    """
    # was    <header class="f" title="Definición de abajo">abajo</header>
    # is now  <h1 class="c-page-header__title" title="Definición de abajo">abajo</h1>
    # LEMA_REGEX_STRING = r'^(?P<lema>[^\W\d_]+)(?P<index>\d+)?(?:,\s+(?P<female_suffix>\w+))?(?:\s+\((' \
    #                     r'?P<related>\w+)\))?$'
    LEMA_REGEX_STRING = r'<.*?\>(?P<lema>.*?)<.*?\>' #todo this needs optional fields added
    lema_re = re.compile(pattern=LEMA_REGEX_STRING, flags=re.IGNORECASE)
    PROCESSING_TAGS = deepcopy(EntryLema.PROCESSING_TAGS)
    PROCESSING_TAGS['lema']['tag'] = 'header'
    PROCESSING_TAGS['lema']['class'] = 'c-page-header__title'

    def __init__(self, html: str):
        """ Initializes a new instance of the ArticleLema class.

        :param html: HTML code that contains an a lema for an article.
        """
        super().__init__(html=html)


    @property
    def female_suffix(self) -> str:
        """ Gets the female form suffix of this lema (if any).
        """
        return self._female_suffix

    @property
    def index(self) -> int:
        """ Gets the ordinal index of the article's lema.
        """
        return self._index

    @property
    def is_acronym(self) -> bool:
        """ Gets a value indicating whether the lema word is an acronym.
        """
        return self._lema.isupper()

    @property
    def is_prefix(self) -> bool:
        """ Gets a value indicating whether the lema word is a prefix.
        """
        return self._lema.startswith('-')

    @property
    def is_suffix(self) -> bool:
        """ Gets a value indicating whether the lema word is a suffix.
        """
        return self._lema.endswith('-')

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict.update({
            'index': self._index,
            'female_suffix': self._female_suffix
        })
        if extended:
            res_dict.update({
                'is_acronym': self.is_acronym,
                'is_prefix': self.is_prefix,
                'is_suffix': self.is_suffix,
            })
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()

        if self._parsed:
            return
        self._reset()
        match = self.lema_re.match(string=self._lema)
        if match:
            self._lema = match['lema']
            if match['index']:
                self._index = int(match['index'])
            if match['female_suffix']:
                self._female_suffix = match['female_suffix'].strip()
        self._parsed = True

    def _reset(self):
        """ Resets fields to a clean state. Needed when resetting the HTML text.
        """
        super()._reset()
        self._index: int = 0
        self._female_suffix: str = ''


class Conjugation(FromHTML):
    """ Represents the conjugation table for a verb.
    """
    # noinspection SpellCheckingInspection
    CONJUGATION_BASE_DICT = {
        'Formas no personales': {
            'Infinitivo': '',
            'Gerundio': '',
            'Participio': ''
        },
        'Indicativo': {
            'Presente': {},
            'Copretérito': {},
            'Pretérito': {},
            'Futuro': {},
            'Pospretérito': {}
        },
        'Subjuntivo': {
            'Presente': {},
            'Futuro': {},
            'Copretérito': {}
        },
        'Imperativo': {}
    }

    def __init__(self, html: str):
        """ Initializes a new instance of the Conjugation class.

        :param html: HTML code that contains the table of a conjugation.
        """
        super().__init__(html=html)


    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Conjugation(id="{self._id}", verb="{self._verb}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return str(self._conjugations)

    @property
    def conjugations(self) -> dict:
        """ Gets the conjugations of a verb.
        """
        return self._conjugations

    @property
    def id(self) -> str:
        """ Gets the ID that matches the conjugation with an article.
        """
        return self._id

    @property
    def verb(self) -> str:
        """ Gets the verb (in infinitive form) of the conjugations.
        """
        return self._verb

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        if extended:
            res_dict['id'] = self._id
        res_dict.update({
            'verb': self._verb,
            'conjugations': self._conjugations
        })
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()

        if self._parsed:
            return
        self._reset()

        if not self._soup.section or not self._soup.section.has_attr('id') or not self._soup.section['id'].startswith('conjugacion'):
            raise Exception('Invalid HTML for a conjugations table.')
        self._id = self._soup.div['id']

        header_tag = self._soup.find(name='header')
        if header_tag:
            verb_tag = header_tag.find(name='h2')
            if verb_tag:
                vt = verb_tag.text
                vt = vt.replace('Conjugación de «', '')
                vt = vt.replace('»', '')
                self._verb = vt

        ### OG was 1 table, new is multiple tables
        table_tags = self._soup.find_all(name='table')

        self._conjugations['Formas no personales'] = {}
        self._conjugations['Formas no personales']["Infinitivo"] = ""
        self._conjugations['Formas no personales']["Gerundio"] = ""
        self._conjugations['Formas no personales']["Participio"] = ""

        self._conjugations['Indicativo'] = {}
        self._conjugations['Indicativo']["Presente"] = {}
        self._conjugations['Indicativo']["Antepresente"] = {}
        self._conjugations['Indicativo']["Copretérito"] = {}
        self._conjugations['Indicativo']["Antecopretérito"] = {}
        self._conjugations['Indicativo']["Pretérito"] = {}
        self._conjugations['Indicativo']["Antepretérito"] = {}
        self._conjugations['Indicativo']["Futuro"] = {}
        self._conjugations['Indicativo']["Antefuturo"] = {}
        self._conjugations['Indicativo']["Pospretérito"] = {}
        self._conjugations['Indicativo']["Antepospretérito"] = {}

        self._conjugations['Subjuntivo'] = {}
        self._conjugations['Subjuntivo']['Presente'] = {}
        self._conjugations['Subjuntivo']['Antepresente'] = {}
        self._conjugations['Subjuntivo']['Pretérito'] = {}
        self._conjugations['Subjuntivo']['Antepretérito'] = {}
        self._conjugations['Subjuntivo']['Futuro'] = {}
        self._conjugations['Subjuntivo']['Antefuturo'] = {}

        self._conjugations['Imperativo'] = {}
        self._conjugations['Imperativo']['Imperativo'] = {}

        # The above could be replaced and the below line used isntead if CONJUGATION_BASE_DICT were updated
        # self._conjugations = deepcopy(self.CONJUGATION_BASE_DICT)

        # Notes:
        # 'Infinitivo compuesto' and 'Gerundio compuesto' are ignored
        # 11 tables, irregular number of columns
        # 0.  infinitive, gerund, Infinitivo compuesto, Gerundio compuesto, Participio
        #     [1,0] = infinitive, [1,1] = gerund
        #     [3,0] = compound infinitive, [3,1] = compound gerund
        #     [5,0] = Participle

        ## Indicative
        # 1.  Presente          Pretérito perfecto compuesto / Antepresente
        #     [1,3] = yo,       [1,4] = yo
        #     [2,2] = tú,       [2,3] = tú
        #     [3,1] = usted,    [3,2] = usted
        #     [4,2] = él,       [4,3] = él
        #     [5,3] = nosotros, [5,4] = nosotros
        #     [6,2] = vosotros, [6,3] = vosotros
        #     [7,1] = ustedes,  [7,2] = ustedes
        #     [8,2] = ellos,    [8,3] = ellos
        # 2.  Pretérito imperfecto / Copretérito    Pretérito pluscuamperfecto / Antecopretérito
        #     [1,3] = yo,                           [1,4] = yo
        #     [2,2] = tú,                           [2,3] = tú
        #     [3,1] = usted,                        [3,2] = usted
        #     [4,2] = él,                           [4,3] = él
        #     [5,3] = nosotros,                     [5,4] = nosotros
        #     [6,2] = vosotros,                     [6,3] = vosotros
        #     [7,1] = ustedes,                      [7,2] = ustedes
        #     [8,2] = ellos,                        [8,3] = ellos
        # 3.  Pretérito perfecto simple / Pretérito Pretérito anterior / Antepretérito
        #     [1,3] = yo,                           [1,4] = yo
        #     [2,2] = tú,                           [2,3] = tú
        #     [3,1] = usted,                        [3,2] = usted
        #     [4,2] = él,                           [4,3] = él
        #     [5,3] = nosotros,                     [5,4] = nosotros
        #     [6,2] = vosotros,                     [6,3] = vosotros
        #     [7,1] = ustedes,                      [7,2] = ustedes
        #     [8,2] = ellos,                        [8,3] = ellos
        # 4.  Futuro simple / Futuro                Futuro compuesto / Antefuturo
        #     [1,3] = yo,                           [1,4] = yo
        #     [2,2] = tú,                           [2,3] = tú
        #     [3,1] = usted,                        [3,2] = usted
        #     [4,2] = él,                           [4,3] = él
        #     [5,3] = nosotros,                     [5,4] = nosotros
        #     [6,2] = vosotros,                     [6,3] = vosotros
        #     [7,1] = ustedes,                      [7,2] = ustedes
        #     [8,2] = ellos,                        [8,3] = ellos
        # 5.  Condicional simple / Pospretérito     Condicional compuesto / Antepospretérito
        #     [1,3] = yo,                           [1,4] = yo
        #     [2,2] = tú,                           [2,3] = tú
        #     [3,1] = usted,                        [3,2] = usted
        #     [4,2] = él,                           [4,3] = él
        #     [5,3] = nosotros,                     [5,4] = nosotros
        #     [6,2] = vosotros,                     [6,3] = vosotros
        #     [7,1] = ustedes,                      [7,2] = ustedes
        #     [8,2] = ellos,                        [8,3] = ellos

        ## Subjunctive
        # 6.  Presente                              Pretérito perfecto compuesto / Antepresente
        #     [1,3] = yo,                           [1,4] = yo
        #     [2,2] = tú,                           [2,3] = tú
        #     [3,1] = usted,                        [3,2] = usted
        #     [4,2] = él,                           [4,3] = él
        #     [5,3] = nosotros,                     [5,4] = nosotros
        #     [6,2] = vosotros,                     [6,3] = vosotros
        #     [7,1] = ustedes,                      [7,2] = ustedes
        #     [8,2] = ellos,                        [8,3] = ellos
        # 7.  Pretérito imperfecto / Pretérito
        #     [1,3] = yo
        #     [2,2] = tú
        #     [3,1] = usted
        #     [4,2] = él
        #     [5,3] = nosotros
        #     [6,2] = vosotros
        #     [7,1] = ustedes
        #     [8,2] = ellos
        # 8.  Pretérito pluscuamperfecto / Antepretérito
        #     [1,3] = yo
        #     [2,2] = tú
        #     [3,1] = usted
        #     [4,2] = él
        #     [5,3] = nosotros
        #     [6,2] = vosotros
        #     [7,1] = ustedes
        #     [8,2] = ellos
        # 9.  Futuro simple / Futuro                Futuro compuesto / Antefuturo
        #     [1,3] = yo,                           [1,4] = yo
        #     [2,2] = tú,                           [2,3] = tú
        #     [3,1] = usted,                        [3,2] = usted
        #     [4,2] = él,                           [4,3] = él
        #     [5,3] = nosotros,                     [5,4] = nosotros
        #     [6,2] = vosotros,                     [6,3] = vosotros
        #     [7,1] = ustedes,                      [7,2] = ustedes
        #     [8,2] = ellos,                        [8,3] = ellos

        ## Imperative
        # 10. Imperativo
        # See below.
        table_index = 0
        for table_tag in table_tags:

            row_index = 0
            for row_tag in table_tag.children:
                for column_index, cell_tag in enumerate(row_tag.contents):
                    # Table 0
                    if table_index == 0 and row_index == 1 and column_index == 0:
                        self._conjugations['Formas no personales']["Infinitivo"] = cell_tag.text.strip()
                    elif table_index == 0 and row_index == 1 and column_index == 1:
                        self._conjugations['Formas no personales']["Gerundio"] = cell_tag.text.strip()
                    elif table_index == 0 and  row_index == 5 and column_index == 0:
                        self._conjugations['Formas no personales']["Participio"] = cell_tag.text.strip()

                    # Table 1
                    elif table_index == 1 and row_index == 1 and column_index == 3:
                        self._conjugations['Indicativo']["Presente"]["yo"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 1 and column_index == 4:
                        self._conjugations['Indicativo']["Antepresente"]["yo"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 2 and column_index == 2:
                        self._conjugations['Indicativo']["Presente"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 2  and column_index == 3:
                        self._conjugations['Indicativo']["Antepresente"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 3 and column_index == 1:
                        self._conjugations['Indicativo']["Presente"]["usted"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 3 and column_index == 2:
                        self._conjugations['Indicativo']["Antepresente"]["usted"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 4 and column_index == 2:
                        self._conjugations['Indicativo']["Presente"]["él"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 4 and column_index == 3:
                        self._conjugations['Indicativo']["Antepresente"]["él"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 5 and column_index == 3:
                        self._conjugations['Indicativo']["Presente"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 5 and column_index == 4:
                        self._conjugations['Indicativo']["Antepresente"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 6 and column_index == 2:
                        self._conjugations['Indicativo']["Presente"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 6 and column_index == 3:
                        self._conjugations['Indicativo']["Antepresente"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 7 and column_index == 1:
                        self._conjugations['Indicativo']["Presente"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 7 and column_index == 2:
                        self._conjugations['Indicativo']["Antepresente"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 8 and column_index == 2:
                        self._conjugations['Indicativo']["Presente"]["ellos"] = cell_tag.text.strip()
                    elif table_index == 1 and row_index == 8 and column_index == 3:
                        self._conjugations['Indicativo']["Antepresente"]["ellos"] = cell_tag.text.strip()

                    # Table 2
                    elif table_index == 2 and row_index == 1 and column_index == 3:
                        self._conjugations['Indicativo']["Copretérito"]["yo"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 1 and column_index == 4:
                        self._conjugations['Indicativo']["Antecopretérito"]["yo"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 2 and column_index == 2:
                        self._conjugations['Indicativo']["Copretérito"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 2 and column_index == 3:
                        self._conjugations['Indicativo']["Antecopretérito"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 3 and column_index == 1:
                        self._conjugations['Indicativo']["Copretérito"]["usted"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 3 and column_index == 2:
                        self._conjugations['Indicativo']["Antecopretérito"]["usted"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 4 and column_index == 2:
                        self._conjugations['Indicativo']["Copretérito"]["él"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 4 and column_index == 3:
                        self._conjugations['Indicativo']["Antecopretérito"]["él"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 5 and column_index == 3:
                        self._conjugations['Indicativo']["Copretérito"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 5 and column_index == 4:
                        self._conjugations['Indicativo']["Antecopretérito"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 6 and column_index == 2:
                        self._conjugations['Indicativo']["Copretérito"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 6 and column_index == 3:
                        self._conjugations['Indicativo']["Antecopretérito"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 7 and column_index == 1:
                        self._conjugations['Indicativo']["Copretérito"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 7 and column_index == 2:
                        self._conjugations['Indicativo']["Antecopretérito"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 8 and column_index == 2:
                        self._conjugations['Indicativo']["Copretérito"]["ellos"] = cell_tag.text.strip()
                    elif table_index == 2 and row_index == 8 and column_index == 3:
                        self._conjugations['Indicativo']["Antecopretérito"]["ellos"] = cell_tag.text.strip()

                    # Table 3
                    elif table_index == 3 and row_index == 1 and column_index == 3:
                        self._conjugations['Indicativo']["Pretérito"]["yo"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 1 and column_index == 4:
                        self._conjugations['Indicativo']["Antepretérito"]["yo"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 2 and column_index == 2:
                        self._conjugations['Indicativo']["Pretérito"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 2 and column_index == 3:
                        self._conjugations['Indicativo']["Antepretérito"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 3 and column_index == 1:
                        self._conjugations['Indicativo']["Pretérito"]["usted"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 3 and column_index == 2:
                        self._conjugations['Indicativo']["Antepretérito"]["usted"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 4 and column_index == 2:
                        self._conjugations['Indicativo']["Pretérito"]["él"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 4 and column_index == 3:
                        self._conjugations['Indicativo']["Antepretérito"]["él"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 5 and column_index == 3:
                        self._conjugations['Indicativo']["Pretérito"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 5 and column_index == 4:
                        self._conjugations['Indicativo']["Antepretérito"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 6 and column_index == 2:
                        self._conjugations['Indicativo']["Pretérito"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 6 and column_index == 3:
                        self._conjugations['Indicativo']["Antepretérito"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 7 and column_index == 1:
                        self._conjugations['Indicativo']["Pretérito"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 7 and column_index == 2:
                        self._conjugations['Indicativo']["Antepretérito"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 8 and column_index == 2:
                        self._conjugations['Indicativo']["Pretérito"]["ellos"] = cell_tag.text.strip()
                    elif table_index == 3 and row_index == 8 and column_index == 3:
                        self._conjugations['Indicativo']["Antepretérito"]["ellos"] = cell_tag.text.strip()

                    # Table 4
                    elif table_index == 4 and row_index == 1 and column_index == 3:
                        self._conjugations['Indicativo']["Futuro"]["yo"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 1 and column_index == 4:
                        self._conjugations['Indicativo']["Antefuturo"]["yo"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 2 and column_index == 2:
                        self._conjugations['Indicativo']["Futuro"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 2 and column_index == 3:
                        self._conjugations['Indicativo']["Antefuturo"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 3 and column_index == 1:
                        self._conjugations['Indicativo']["Futuro"]["usted"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 3 and column_index == 2:
                        self._conjugations['Indicativo']["Antefuturo"]["usted"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 4 and column_index == 2:
                        self._conjugations['Indicativo']["Futuro"]["él"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 4 and column_index == 3:
                        self._conjugations['Indicativo']["Antefuturo"]["él"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 5 and column_index == 3:
                        self._conjugations['Indicativo']["Futuro"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 5 and column_index == 4:
                        self._conjugations['Indicativo']["Antefuturo"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 6 and column_index == 2:
                        self._conjugations['Indicativo']["Futuro"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 6 and column_index == 3:
                        self._conjugations['Indicativo']["Antefuturo"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 7 and column_index == 1:
                        self._conjugations['Indicativo']["Futuro"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 7 and column_index == 2:
                        self._conjugations['Indicativo']["Antefuturo"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 8 and column_index == 2:
                        self._conjugations['Indicativo']["Futuro"]["ellos"] = cell_tag.text.strip()
                    elif table_index == 4 and row_index == 8 and column_index == 3:
                        self._conjugations['Indicativo']["Antefuturo"]["ellos"] = cell_tag.text.strip()

                    # Table 5
                    elif table_index == 5 and row_index == 1 and column_index == 3:
                        self._conjugations['Indicativo']["Pospretérito"]["yo"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 1 and column_index == 4:
                        self._conjugations['Indicativo']["Antepospretérito"]["yo"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 2 and column_index == 2:
                        self._conjugations['Indicativo']["Pospretérito"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 2 and column_index == 3:
                        self._conjugations['Indicativo']["Antepospretérito"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 3 and column_index == 1:
                        self._conjugations['Indicativo']["Pospretérito"]["usted"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 3 and column_index == 2:
                        self._conjugations['Indicativo']["Antepospretérito"]["usted"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 4 and column_index == 2:
                        self._conjugations['Indicativo']["Pospretérito"]["él"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 4 and column_index == 3:
                        self._conjugations['Indicativo']["Antepospretérito"]["él"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 5 and column_index == 3:
                        self._conjugations['Indicativo']["Pospretérito"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 5 and column_index == 4:
                        self._conjugations['Indicativo']["Antepospretérito"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 6 and column_index == 2:
                        self._conjugations['Indicativo']["Pospretérito"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 6 and column_index == 3:
                        self._conjugations['Indicativo']["Antepospretérito"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 7 and column_index == 1:
                        self._conjugations['Indicativo']["Pospretérito"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 7 and column_index == 2:
                        self._conjugations['Indicativo']["Antepospretérito"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 8 and column_index == 2:
                        self._conjugations['Indicativo']["Pospretérito"]["ellos"] = cell_tag.text.strip()
                    elif table_index == 5 and row_index == 8 and column_index == 3:
                        self._conjugations['Indicativo']["Antepospretérito"]["ellos"] = cell_tag.text.strip()

                    # Table 6
                    elif table_index == 6 and row_index == 1 and column_index == 3:
                        self._conjugations['Subjuntivo']["Presente"]["yo"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 1 and column_index == 4:
                        self._conjugations['Subjuntivo']["Antepresente"]["yo"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 2 and column_index == 2:
                        self._conjugations['Subjuntivo']["Presente"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 2 and column_index == 3:
                        self._conjugations['Subjuntivo']["Antepresente"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 3 and column_index == 1:
                        self._conjugations['Subjuntivo']["Presente"]["usted"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 3 and column_index == 2:
                        self._conjugations['Subjuntivo']["Antepresente"]["usted"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 4 and column_index == 2:
                        self._conjugations['Subjuntivo']["Presente"]["él"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 4 and column_index == 3:
                        self._conjugations['Subjuntivo']["Antepresente"]["él"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 5 and column_index == 3:
                        self._conjugations['Subjuntivo']["Presente"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 5 and column_index == 4:
                        self._conjugations['Subjuntivo']["Antepresente"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 6 and column_index == 2:
                        self._conjugations['Subjuntivo']["Presente"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 6 and column_index == 3:
                        self._conjugations['Subjuntivo']["Antepresente"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 7 and column_index == 1:
                        self._conjugations['Subjuntivo']["Presente"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 7 and column_index == 2:
                        self._conjugations['Subjuntivo']["Antepresente"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 8 and column_index == 2:
                        self._conjugations['Subjuntivo']["Presente"]["ellos"] = cell_tag.text.strip()
                    elif table_index == 6 and row_index == 8 and column_index == 3:
                        self._conjugations['Subjuntivo']["Antepresente"]["ellos"] = cell_tag.text.strip()

                    # Table 7
                    elif table_index == 7 and row_index == 1 and column_index == 3:
                        self._conjugations['Subjuntivo']["Pretérito"]["yo"] = cell_tag.text.strip()
                    elif table_index == 7 and row_index == 2 and column_index == 2:
                        self._conjugations['Subjuntivo']["Pretérito"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 7 and row_index == 3 and column_index == 1:
                        self._conjugations['Subjuntivo']["Pretérito"]["usted"] = cell_tag.text.strip()
                    elif table_index == 7 and row_index == 4 and column_index == 2:
                        self._conjugations['Subjuntivo']["Pretérito"]["él"] = cell_tag.text.strip()
                    elif table_index == 7 and row_index == 5 and column_index == 3:
                        self._conjugations['Subjuntivo']["Pretérito"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 7 and row_index == 6 and column_index == 2:
                        self._conjugations['Subjuntivo']["Pretérito"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 7 and row_index == 7 and column_index == 1:
                        self._conjugations['Subjuntivo']["Pretérito"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 7 and row_index == 8 and column_index == 2:
                        self._conjugations['Subjuntivo']["Pretérito"]["ellos"] = cell_tag.text.strip()

                    # Table 8
                    elif table_index == 8 and row_index == 1 and column_index == 3:
                        self._conjugations['Subjuntivo']["Antepretérito"]["yo"] = cell_tag.text.strip()
                    elif table_index == 8 and row_index == 2 and column_index == 2:
                        self._conjugations['Subjuntivo']["Antepretérito"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 8 and row_index == 3 and column_index == 1:
                        self._conjugations['Subjuntivo']["Antepretérito"]["usted"] = cell_tag.text.strip()
                    elif table_index == 8 and row_index == 4 and column_index == 2:
                        self._conjugations['Subjuntivo']["Antepretérito"]["él"] = cell_tag.text.strip()
                    elif table_index == 8 and row_index == 5 and column_index == 3:
                        self._conjugations['Subjuntivo']["Antepretérito"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 8 and row_index == 6 and column_index == 2:
                        self._conjugations['Subjuntivo']["Antepretérito"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 8 and row_index == 7 and column_index == 1:
                        self._conjugations['Subjuntivo']["Antepretérito"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 8 and row_index == 8 and column_index == 2:
                        self._conjugations['Subjuntivo']["Antepretérito"]["ellos"] = cell_tag.text.strip()

                    # Table 9
                    elif table_index == 9 and row_index == 1 and column_index == 3:
                        self._conjugations['Subjuntivo']["Futuro"]["yo"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 1 and column_index == 4:
                        self._conjugations['Subjuntivo']["Antefuturo"]["yo"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 2 and column_index == 2:
                        self._conjugations['Subjuntivo']["Futuro"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 2 and column_index == 3:
                        self._conjugations['Subjuntivo']["Antefuturo"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 3 and column_index == 1:
                        self._conjugations['Subjuntivo']["Futuro"]["usted"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 3 and column_index == 2:
                        self._conjugations['Subjuntivo']["Antefuturo"]["usted"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 4 and column_index == 2:
                        self._conjugations['Subjuntivo']["Futuro"]["él"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 4 and column_index == 3:
                        self._conjugations['Subjuntivo']["Antefuturo"]["él"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 5 and column_index == 3:
                        self._conjugations['Subjuntivo']["Futuro"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 5 and column_index == 4:
                        self._conjugations['Subjuntivo']["Antefuturo"]["nosotros"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 6 and column_index == 2:
                        self._conjugations['Subjuntivo']["Futuro"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 6 and column_index == 3:
                        self._conjugations['Subjuntivo']["Antefuturo"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 7 and column_index == 1:
                        self._conjugations['Subjuntivo']["Futuro"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 7 and column_index == 2:
                        self._conjugations['Subjuntivo']["Antefuturo"]["ustedes"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 8 and column_index == 2:
                        self._conjugations['Subjuntivo']["Futuro"]["ellos"] = cell_tag.text.strip()
                    elif table_index == 9 and row_index == 8 and column_index == 3:
                        self._conjugations['Subjuntivo']["Antefuturo"]["ellos"] = cell_tag.text.strip()

                    #Table 10
                    elif table_index == 10 and row_index == 1 and column_index == 3:
                        self._conjugations['Imperativo']["Imperativo"]["tú / vos"] = cell_tag.text.strip()
                    elif table_index == 10 and row_index == 2 and column_index == 1:
                        self._conjugations['Imperativo']["Imperativo"]["usted"] = cell_tag.text.strip()
                    elif table_index == 10 and row_index == 3 and column_index == 3:
                        self._conjugations['Imperativo']["Imperativo"]["vosotros"] = cell_tag.text.strip()
                    elif table_index == 10 and row_index == 4 and column_index == 1:
                        self._conjugations['Imperativo']["Imperativo"]["ustedes"] = cell_tag.text.strip()

                row_index += 1
            table_index += 1
        self._parsed = True

    def _reset(self):
        """ Resets fields to a clean state. Needed when resetting the HTML text.
        """
        self._id: str = ''
        self._verb: str = ''
        self._conjugations: dict = {}


class Article(Entry):
    """ Represents an article, which contains simple entries and complex forms.
    """
    _LEMA_CLASS = ArticleLema
    PROCESSING_TAGS = deepcopy(Entry.PROCESSING_TAGS)
    PROCESSING_TAGS['definition']['class'] = 'j'
    PROCESSING_TAGS['other'] = {
        'tag': 'p',
        'class': 'l'
    }

    def __init__(self, html: str):
        """ Initializes a new instance of the Article class.

        :param html: HTML code that contains a definition.
        """
        super().__init__(html=html)


    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Article(id="{self._id}", lema="{self.lema.lema}", raw_text="{self._raw_text}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._raw_text

    @property
    def complex_forms(self) -> Sequence[Entry]:
        """ Gets a sequence of entries representing complex forms of the lema word.
        """
        return self._complex_forms

    @property
    def id(self) -> str:
        """ Gets the ID of the article.
        """
        return self._id

    @property
    def is_verb(self) -> bool:
        """ Gets a value indicating whether the article has conjugations or an entry that is a verb.
        """
        return self.conjugations is not None or any(definition for definition in self.definitions
                                                    if definition.is_verb)

    @property
    def lema(self) -> ArticleLema:
        """ Gets the lema for this article.
        """
        return self._lema

    @property
    def other_entries(self) -> Sequence[Word]:
        """ Gets a sequence of words representing related entries with corresponding links to fetch their results.
        """
        return self._other_entries

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super(Entry, self).to_dict(extended=extended)
        res_dict.update({
            'id': self._id,
            'lema': self.lema.to_dict(extended=extended),
            'supplementary_info': [s.to_dict(extended=extended) for s in self._supplementary_info],
            'is': {
              'verb': self.is_verb
            },
            'definitions': [definition.to_dict(extended=extended) for definition in self._definitions],
            'complex_forms': [complex_form.to_dict(extended=extended) for complex_form in self._complex_forms],
            'other_entries': [entry.to_dict(extended=extended) for entry in self._other_entries]
        })
        if self.conjugations:
            res_dict['conjugations'] = self.conjugations.to_dict(extended=extended)
        if extended:
            res_dict['raw_text'] = self._raw_text
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super(Entry, self)._parse_html()

        if self._parsed:
            return
        self._reset()
        if not self._soup.article or not self._soup.article.header:
            raise Exception('Invalid HTML.')

        self._raw_text = self._soup.get_text()
        if self._soup.article.has_attr('id'):
            self._id = self._soup.article['id']

        lema_entry_tag = Tag(name='lema_entry')
        complex_form_tag: Optional[Tag] = None
        complex_forms_tags: List[Tag] = []

        tag_containing_lema = self._soup.article.select("h1.c-page-header__title")
        lema_entry_tag.append(tag_containing_lema[0])

        matching_descendants = self._soup.article.find_all(
            class_=['f', 'j', 'j1', 'j2', 'k5', 'k6', 'l', 'l2', 'l3', 'm', 'n1', 'n2', 'n3', 'n4', 'n5'])

        index = 0
        for tag in matching_descendants:

            if tag.name == 'div' and ('n2' in tag.get('class', []) \
                    or 'n1' in tag.get('class', []) \
                                      or 'n4' in tag.get('class', []) \
                                      or 'n5' in tag.get('class', []) \
                                      or 'n3' in tag.get('class', [])):
                if complex_form_tag is not None:
                    complex_form_tag.append(tag)
                else:
                    lema_entry_tag.append(tag)
            elif (tag.name == 'li' and 'j' in tag.get('class', [])) \
                    or (tag.name == 'li' and 'j1' in tag.get('class', [])) \
                    or (tag.name == 'li' and 'j2' in tag.get('class', [])):

                if complex_form_tag is not None:
                    complex_form_tag.append(tag)
                else:
                    lema_entry_tag.append(tag)
            elif tag.name == 'h3' and ('k6' in tag.get('class', []) or 'k5' in tag.get('class', [])):
                pass
                complex_form_tag = Tag(name='complex_form_entry')
                complex_forms_tags.append(complex_form_tag)
                complex_form_tag.append(tag)
            elif tag.name == 'li' and 'm' in tag.get('class', []):
                pass
                if complex_form_tag:
                    complex_form_tag.append(tag)
                else:
                    complex_form_tag = Tag(name='complex_form_entry')
            elif tag.name == 'h3' and ('l3' in tag.get('class', []) \
                                       or 'l2' in tag.get('class', []) \
                                       or 'l' in tag.get('class', [])):
                self._other_entries.append(Word(html=str(tag), parent_href=self._id))
            index += 1

        self._process_entry(entry_tag=lema_entry_tag)
        for complex_form_tag in complex_forms_tags:
            self._complex_forms.append(Entry(html=str(complex_form_tag)))
        self._parsed = True


    def _reset(self):
        """ Resets fields to a clean state. Needed when resetting the HTML text.
        """
        super()._reset()
        self._id: str = ''
        self._lema: Optional[ArticleLema] = None
        self._complex_forms: List[Entry] = []
        self._other_entries: List[Word] = []
        self.conjugations: Optional[Conjugation] = None


class SearchResult(FromHTML):
    """ Represents the result of a search.
    """
    __INDEX_REGEX_STRING = r'^(?P<lema>\D*)(?P<index>\d+)$'
    __index_re = re.compile(pattern=__INDEX_REGEX_STRING, flags=re.IGNORECASE)

    def __init__(self, html: str):
        """ Initializes a new instance of the SearchResult class.

        :param html: HTML code that contains a definition.
        """
        super().__init__(html=html)

    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'SearchResult(title="{self._title}", canonical="{self._canonical}", ' \
               f'meta_description="{self._meta_description}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._meta_description

    @property
    def articles(self) -> Sequence[Article]:
        """ Gets a sequence with all articles contained in the search result.
        """
        return self._articles

    @property
    def canonical(self) -> str:
        """ Gets the canonical link that returns this search result.
        """
        return self._canonical

    @property
    def meta_description(self) -> str:
        """ Gets the full one-line description of the search result.
        """
        return self._meta_description

    @property
    def related_entries(self) -> dict:
        """ Gets related entries (if any) in case no articles are returned from the search.
        """
        return self._related_entries

    @property
    def title(self) -> str:
        """ Gets the title of the search result.
        """
        return self._title

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict['title'] = self._title

        print('SearchResult :: to_dict')

        if extended:
            res_dict.update({
                'canonical': self._canonical,
                'meta_description': self._meta_description
            })
        if self._articles:
            res_dict['articles'] = [article.to_dict(extended=extended) for article in self._articles]
        elif self._related_entries:
            res_dict['related_entries'] = {k: [w.to_dict(extended=extended) for w in v]
                                           for k, v in self._related_entries.items()}
        res_dict['synonyms'] = self.synonyms
        res_dict['antonyms'] = self.antonyms

        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()

        if self._parsed:
            return
        self._reset()

        canonical_tag = self._soup.find(name='link', attrs={'ref': 'canonical'})
        if canonical_tag:
            self._canonical = canonical_tag['href']
        if self._soup.title:
            self._title = str(self._soup.title.text)
        meta_description_tag = self._soup.find(name='meta', attrs={'name': 'description'})
        if meta_description_tag:
            self._meta_description = meta_description_tag['content']

        results_div_tag = self._soup.find(name='div', attrs={'id': 'resultados'})
        if results_div_tag:
            for article_tag in results_div_tag.find_all(name='article', recursive=False):
                article = Article(html=str(article_tag))
                self._articles.append(article)

        if self._parsed:
            log_exit('SearchResult :: _parse_html (already parsed)')
            return
        self._reset()

        canonical_tag = self._soup.find(name='link', attrs={'ref': 'canonical'})
        if canonical_tag:
            self._canonical = canonical_tag['href']
        if self._soup.title:
            self._title = str(self._soup.title.text)
        meta_description_tag = self._soup.find(name='meta', attrs={'name': 'description'})
        if meta_description_tag:
            self._meta_description = meta_description_tag['content']

        results_div_tag = self._soup.find(name='div', attrs={'id': 'resultados'})

        if results_div_tag:


            if results_div_tag.find_all(name='article', recursive=False) != []:
                assert len(results_div_tag.find_all(name='article', recursive=False)) == 1
                #This is majority of pages, where article is at top level and there is only one
                for article_tag in results_div_tag.find_all(name='article', recursive=False):
                    article = Article(html=str(article_tag))
                    self._articles.append(article)


                    conjugations_tag = None
                    try:
                        conjugations_tag = article_tag.select('[id^="conjugacion"]')[0]
                    except Exception:
                        pass

                    if conjugations_tag:
                        conjugations = Conjugation(html=str(conjugations_tag))
                        article.conjugations = conjugations
            else:
                #There are no direct children which are article tags
                for article_tag in results_div_tag.find_all(name='article', recursive=True):
                    article = Article(html=str(article_tag))
                    self._articles.append(article)

                    # noinspection SpellCheckingInspection
                    conjugations_tag = None
                    try:
                        conjugations_tag = article_tag.select('[id^="conjugacion"]')[0]
                    except Exception:
                        pass

                    if conjugations_tag:
                        conjugations = Conjugation(html=str(conjugations_tag))
                        article.conjugations = conjugations

            synonym_section = self._soup.find_all("section", attrs={"id": re.compile(r"^sinonimos")})
            synonym_ul = synonym_section[0].find_all("ul", attrs={"class": "c-related-words"})

            synonym_list = []
            for syn in synonym_ul[0].descendants:
                if syn.name is None:
                    syn_text = syn.text.replace(',','').replace('.','').strip().replace('0','')
                    syn_text = syn_text.replace('1','').replace('2','').replace('3','')
                    syn_text = syn_text.replace('4', '').replace('5', '').replace('6', '')
                    syn_text = syn_text.replace('7', '').replace('8', '').replace('9', '')
                    if syn_text != '':
                        synonym_list.append(syn_text)
            self.synonyms = synonym_list

            antonym_section_section = self._soup.find_all("section", attrs={"id": re.compile(r"^antonimos")})
            antonym_ul = antonym_section_section[0].find_all("ul", attrs={"class": "c-related-words"})

            antonym_list = []
            for ant in antonym_ul[0].descendants:
                if ant.name is None:
                    ant_text = ant.text.replace(',', '').replace('.', '').strip().replace('0', '')
                    ant_text = ant_text.replace('1', '').replace('2', '').replace('3', '')
                    ant_text = ant_text.replace('4', '').replace('5', '').replace('6', '')
                    ant_text = ant_text.replace('7', '').replace('8', '').replace('9', '')
                    if ant_text != '':
                        antonym_list.append(ant_text)
            self.antonyms = antonym_list

        self._parsed = True

    def _reset(self):
        """ Resets fields to a clean state. Needed when resetting the HTML text.
        """
        self._articles: List[Article] = []
        self._title: str = ''
        self._canonical: str = ''
        self._meta_description: str = ''
        self._related_entries: dict = {}
