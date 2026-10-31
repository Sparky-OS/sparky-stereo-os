#include <algorithm>
#include <iostream>
#include <map>
#include <string>
#include <vector>
int main(int argc, char **argv) {
    std::vector<std::string> words(argv, argv + argc);
    std::sort(words.begin(), words.end());
    std::map<std::string, int> count;
    for (const auto &w : words) ++count[w];
    for (const auto &[w, n] : count) std::cout << w << ' ' << n << '\n';
}
